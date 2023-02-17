import math, time, logging
from datetime import datetime
import threading, collections, queue, os, os.path
from kafka import KafkaProducer
import deepspeech
import numpy as np
import pyaudio, audioop
import wave
from halo import Halo
from scipy import signal
import json

import sounddevice as sd

logging.basicConfig(level=20)

def decibel( data, width ):
    rms = audioop.rms(data, width)
    if rms == 0:
        return 0
    else:
        return 20 * math.log(rms, 10)

def rescaled_decibel( data, width ):
    rms = audioop.rms(data, width)
    if rms == 0:
        return 0
    else:
        decibel = 20 * math.log(rms, 10)
        return math.tanh( (decibel - 70) * 0.05 )

class Audio(object):
    """Streams raw audio from microphone. Data is received in a separate thread, and stored in a buffer, to be read from."""

    FORMAT = pyaudio.paInt16
    # Network/VAD rate-space
    RATE_PROCESS = 16000
    CHANNELS = 1
    BLOCKS_PER_SECOND = 50

    def __init__(self, callback=None, device=None, input_rate=RATE_PROCESS, file=None):
        def proxy_callback(in_data, frame_count, time_info, status):
            #pylint: disable=unused-argument
            if self.chunk is not None:
                in_data = self.wf.readframes(self.chunk)
            callback(in_data)
            return (None, pyaudio.paContinue)
        if callback is None: callback = lambda in_data: self.buffer_queue.put(in_data)
        self.buffer_queue = queue.Queue()
        self.device = device
        self.input_rate = input_rate
        self.sample_rate = self.RATE_PROCESS
        self.block_size = int(self.RATE_PROCESS / float(self.BLOCKS_PER_SECOND))
        self.block_size_input = int(self.input_rate / float(self.BLOCKS_PER_SECOND))
        self.pa = pyaudio.PyAudio()

        kwargs = {
            'format': self.FORMAT,
            'channels': self.CHANNELS,
            'rate': self.input_rate,
            'input': True,
            'frames_per_buffer': self.block_size_input,
            'stream_callback': proxy_callback,
        }

        self.chunk = None
        # if not default device
        if self.device:
            kwargs['input_device_index'] = self.device
        elif file is not None:
            self.chunk = 320
            self.wf = wave.open(file, 'rb')

        self.stream = self.pa.open(**kwargs)
        self.stream.start_stream()

    def resample(self, data, input_rate):
        """
        Microphone may not support our native processing sampling rate, so
        resample from input_rate to RATE_PROCESS here for webrtcvad and
        deepspeech

        Args:
            data (binary): Input audio stream
            input_rate (int): Input audio rate to resample from
        """
        data16 = np.fromstring(string=data, dtype=np.int16)
        resample_size = int(len(data16) / self.input_rate * self.RATE_PROCESS)
        resample = signal.resample(data16, resample_size)
        resample16 = np.array(resample, dtype=np.int16)
        return resample16.tostring()

    def read_resampled(self):
        """Return a block of audio data resampled to 16000hz, blocking if necessary."""
        return self.resample(data=self.buffer_queue.get(),
                             input_rate=self.input_rate)

    def read(self):
        """Return a block of audio data, blocking if necessary."""
        return self.buffer_queue.get()

    def destroy(self):
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()

    frame_duration_ms = property(lambda self: 1000 * self.block_size // self.sample_rate)

    def write_wav(self, filename, data):
        logging.info("write wav %s", filename)
        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.CHANNELS)
        assert self.FORMAT == pyaudio.paInt16
        wf.setsampwidth(2)
        wf.setframerate(self.sample_rate)
        wf.writeframes(data)
        wf.close()


class VADAudio(Audio):
    """Filter & segment audio with voice activity detection."""

    def __init__(self, device=None, input_rate=None, file=None):
        super().__init__(device=device, input_rate=input_rate, file=file)

    def frame_generator(self):
        """Generator that yields all audio frames from microphone."""
        if self.input_rate == self.RATE_PROCESS:
            while True:
                yield self.read()
        else:
            while True:
                yield self.read_resampled()

    def vad_collector(self, padding_ms=1000, ratio=0.70, frames=None):
        """Generator that yields series of consecutive audio frames comprising each utterence, separated by yielding a single None.
            Determines voice activity by ratio of frames in padding_ms. Uses a buffer to include padding_ms prior to being triggered.
            Example: (frame, ..., frame, None, frame, ..., frame, None, ...)
                      |---utterence---|        |---utterence---|
        """
        if frames is None: frames = self.frame_generator()
        num_padding_frames = padding_ms // self.frame_duration_ms
        ring_buffer = collections.deque(maxlen=num_padding_frames)
        triggered = False

        for frame in frames:
            if len(frame) < 640:
                return
            
            input_level = rescaled_decibel(frame, 2)
            is_speech = input_level > 0.0

            if not triggered:
                ring_buffer.append((frame, is_speech))
                num_voiced = len([f for f, speech in ring_buffer if speech])

                if num_voiced > ratio * ring_buffer.maxlen:
                    print()
                    print(f"[VAD] Triggered! The number of frames louder than threshold in buffer({num_voiced}/{ring_buffer.maxlen}) exceed the given ratio")
                    print()
                    triggered = True
                    for f, s in ring_buffer:
                        yield f
                    ring_buffer.clear()

            else:
                yield frame
                ring_buffer.append((frame, is_speech))
                num_unvoiced = len([f for f, speech in ring_buffer if not speech])
                if num_unvoiced > ratio * ring_buffer.maxlen:
                    triggered = False
                    yield None
                    ring_buffer.clear()

def main(ARGS):
    # Set Kafka Producer
    print()
    print("[Kafka] Setting kafka producer...")
    producer = KafkaProducer(bootstrap_servers=[f'{ARGS.host_ip}:9092'])
    print()

    # Load DeepSpeech model
    if os.path.isdir(ARGS.model):
        model_dir = ARGS.model
        ARGS.model = os.path.join(model_dir, 'output_graph.pb')
        ARGS.scorer = os.path.join(model_dir, ARGS.scorer)

    print('[DeepSpeech] Initializing model...')
    logging.info("ARGS.model: %s", ARGS.model)
    model = deepspeech.Model(ARGS.model)
    if ARGS.scorer:
        logging.info("ARGS.scorer: %s", ARGS.scorer)
        model.enableExternalScorer(ARGS.scorer)

    # Start audio with VAD
    print()
    print('[DeepSpeech] Start model with VAD...')
    vad_audio = VADAudio(device=ARGS.device,
                         input_rate=ARGS.rate,
                         file=ARGS.file)
    print()
    print("[DeepSpeech] Listening (ctrl-C to exit)...")
    frames = vad_audio.vad_collector()

    # Stream from microphone to DeepSpeech using VAD
    spinner = None
    if not ARGS.nospinner:
        spinner = Halo(spinner='line')
    stream_context = model.createStream()
    wav_data = bytearray()
    for frame in frames:
        if frame is not None:
            if spinner: spinner.start()
            logging.debug("streaming frame")
            stream_context.feedAudioContent(np.frombuffer(frame, np.int16))
            if ARGS.savewav: wav_data.extend(frame)
            res = {'ts': datetime.now().strftime('%H:%M:%S.%f'),
                    'streaming': True,
                    'confidence': 0,
                    'sentence': ''}
            json.dump(res, open('server/res_stt.json', 'w'))
        else:
            if spinner: spinner.stop()
            logging.debug("end utterence")
            if ARGS.savewav:
                vad_audio.write_wav(os.path.join(ARGS.savewav, datetime.now().strftime("savewav_%Y-%m-%d_%H-%M-%S_%f.wav")), wav_data)
                wav_data = bytearray()
            recognized = stream_context.finishStreamWithMetadata()
            best_transcript = sorted( recognized.transcripts, key=lambda candidate: candidate.confidence, reverse=True )[0] # Select best candidate with highest confidence
            sentence = ''.join([token_data.text for token_data in best_transcript.tokens])
            confidence = best_transcript.confidence
            if len(sentence) == 0:
                print(f"[DeepSpeech] Recognized empty sentence!")
            elif len(sentence) > 0 and confidence < -50.0 :
                print(f"[DeepSpeech] Recognized sentence with low confidence! ({confidence}))")
                print(f"[DeepSpeech] Recognized sentence: {sentence}")
            else:
                print(f"[DeepSpeech] Recognized sentence: {sentence}")
                print(f"[DeepSpeech]                      confidence = {confidence}")
                print()
                producer.send(ARGS.topic, sentence.encode(encoding='utf-8'))
                producer.flush()
                print(f"[Kafka Producer]({datetime.now()}) Sentence detected and sent to GCP Kafka broker.")
                
            res = {'ts': datetime.now().strftime('%H:%M:%S.%f'),
                    'streaming': False,
                    'confidence': confidence,
                   'sentence': sentence}
            json.dump(res, open('server/res_stt.json', 'w'))


            print()
            stream_context = model.createStream()


if __name__ == '__main__':
    DEFAULT_SAMPLE_RATE = 16000

    import argparse
    parser = argparse.ArgumentParser(description="Stream from microphone to DeepSpeech using VAD")

    # DeepSpeech model configuration
    parser.add_argument('--nospinner', action='store_true',
                        help="Disable spinner")
    parser.add_argument('-w', '--savewav',
                        help="Save .wav files of utterences to given directory")
    parser.add_argument('-f', '--file',
                        help="Read from .wav file instead of microphone")

    parser.add_argument('-m', '--model', required=True,
                        help="Path to the model (protocol buffer binary file, or entire directory containing all standard-named files for model)")
    parser.add_argument('-s', '--scorer',
                        help="Path to the external scorer file.")
    parser.add_argument('-d', '--device', type=int, default=None,
                        help="Device input index (Int) as listed by pyaudio.PyAudio.get_device_info_by_index(). If not provided, falls back to PyAudio.get_default_device().")
    parser.add_argument('-r', '--rate', type=int, default=DEFAULT_SAMPLE_RATE,
                        help=f"Input device sample rate. Default: {DEFAULT_SAMPLE_RATE}. Your device may require 44100.")

    # Config path for kafka system setting
    parser.add_argument('-p', '--config-path', type=str, default='config.json')
    parser.add_argument('-i', '--bulb-id', type=int, default = 1, help="either 1 or 2")

    ARGS = parser.parse_args()
    
    with open("config.json", "r") as f:
        config = json.load(f)

    ARGS.host_ip = config["GCP_IP"]
    ARGS.topic = config[f"EMOTION_TOPIC{ARGS.bulb_id}"]

    if ARGS.savewav: os.makedirs(ARGS.savewav, exist_ok=True)
    main(ARGS)
