#!/usr/bin/python
import RPi.GPIO as GPIO
import time

#GPIO SETUP
channel = 24
GPIO.setmode(GPIO.BCM)
GPIO.setup(channel, GPIO.IN)

def callback(channel):
        if GPIO.input(channel):
                print ("Helm Terjatuh!")
        else:
                print("Helm Terjatuh!")

GPIO.add_event_detect(channel, GPIO.BOTH, bouncetime=600)
GPIO.add_event_callback(channel, callback)


while True:
        time.sleep(1)