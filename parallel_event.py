# coding:utf-8
import time
from ctypes import windll
P = windll.inpoutx64

LPT1_addr = 0x8FF8
LPT2_addr = 0x4FF8

def ParallelSendCode(code):
    P.Out32(0x8FF8, int(code))
    P.Out32(0x4FF8, int(code))
    time.sleep(0.005)
    P.Out32(0x8FF8, 0)
    P.Out32(0x4FF8, 0)
    print(code)


# for i in range(100):
#     ParallelSendCode(i+1)
#     print(i+1)
#     time.sleep(0.5)
