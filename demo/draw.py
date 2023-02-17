import matplotlib.pyplot as plt 
import matplotlib.animation as animation
import matplotlib.dates as mdates

import json
from datetime import datetime
import time

time_window = 50
threshold = 0.0

def frame(res1, res2):
    void_time = datetime.strptime(datetime.now().time().strftime('%H:%M:%S.%f'), '%H:%M:%S.%f')
    x = [void_time] * time_window
    pi9_dec = [0] * time_window 
    pi9_dec_rescaled = [0] * time_window
    pi9_thres = [0] * time_window

    pi10_dec = [0] * time_window 
    pi10_dec_rescaled = [0] * time_window
    pi10_thres = [0] * time_window

    fig, ax = plt.subplots(nrows=4, ncols=2, sharex=True,
                           gridspec_kw={'height_ratios': [1, 3, 3, 3]})
    #fig.suptitle('Real-Time Visualization', fontsize=15, fontweight='bold')
    fig.tight_layout(pad=1.25)
    fig.show()
    fig.canvas.draw()

    #date_formatter = mdates.DateFormatter('%H:%M:%S.%f')
    while True:
        try:
            res_pi9 = json.load(open(res1, 'r'))
            res_pi10 = json.load(open(res2, 'r'))
        except:
            time.sleep(1)

        x.append(datetime.strptime(res_pi9['ts'], '%H:%M:%S.%f'))
        #x.append(res['ts'])
        pi9_dec.append(res_pi9['db'])
        pi9_dec_rescaled.append(res_pi9['db_rescale'])
        pi9_thres.append(1 if res_pi9['db_rescale'] > threshold else 0)

        pi10_dec.append(res_pi10['db'])
        pi10_dec_rescaled.append(res_pi10['db_rescale'])
        pi10_thres.append(1 if res_pi10['db_rescale'] > threshold else 0)

        if len(x) > time_window:
            x = x[-time_window:]
            pi9_dec = pi9_dec[-time_window:]
            pi9_dec_rescaled = pi9_dec_rescaled[-time_window:]
            pi9_thres = pi9_thres[-time_window:]

            pi10_dec = pi10_dec[-time_window:]
            pi10_dec_rescaled = pi10_dec_rescaled[-time_window:]
            pi10_thres = pi10_thres[-time_window:]

            ax[1, 0].cla()
            ax[2, 0].cla()
            ax[3, 0].cla()
            ax[1, 1].cla()
            ax[2, 1].cla()
            ax[3, 1].cla()

        # pi9
        ax[1, 0].set_title('Decibel', loc='center')
        ax[1, 0].plot(x, pi9_dec, marker='o', color='b')

        ax[2, 0].set_title('Decibel (Rescaled)', loc='center')
        ax[2, 0].plot(x, [0.0]*len(x), color='r', linestyle=':')
        ax[2, 0].plot(x, pi9_dec_rescaled, marker='o', color='b')
        ax[2, 0].set_ylim([-1, 1])

        ax[3, 0].set_title('Exceed Threshold')
        if pi9_thres[-1] == 1:
            ax[3, 0].plot(x, pi9_thres, color='green')
        else:
            ax[3, 0].plot(x, pi9_thres, color='red')
        ax[3, 0].set_ylim([-0.1, 1.1])

        # pi10
        ax[1, 1].set_title('Decibel', loc='center')
        ax[1, 1].plot(x, pi10_dec, marker='o', color='b')

        ax[2, 1].set_title('Decibel (Rescaled)', loc='center')
        ax[2, 1].plot(x, [0.0]*len(x), color='r', linestyle=':')
        ax[2, 1].plot(x, pi10_dec_rescaled, marker='o', color='b')
        ax[2, 1].set_ylim([-1, 1])

        ax[3, 1].set_title('Exceed Threshold')
        if pi10_thres[-1] == 1:
            ax[3, 1].plot(x, pi10_thres, color='green')
        else:
            ax[3, 1].plot(x, pi10_thres, color='red')
        ax[3, 1].set_ylim([-0.1, 1.1])

        ax[0, 0].axis('off')
        ax[0, 0].set_title('Pi 9', fontweight='bold', fontsize=12, y=-.01)

        ax[0, 1].axis('off')
        ax[0, 1].set_title('Pi 10', fontweight='bold', fontsize=12, y=-.01)

        plt.pause(0.01)
        #plt.xticks(rotation=45)
        fig.subplots_adjust(hspace=0.5, bottom=0.1)
        fig.canvas.draw()



if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--response_first', type=str)
    parser.add_argument('--response_second', type=str)
    args = parser.parse_args()

    frame(args.response_first, args.response_second)
