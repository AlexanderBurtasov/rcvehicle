import machine
import servo
import _thread
import time

class EscControl:
    def __init__(self, pinNum, sleepInterval, rotationSpeed):
        self.servo = servo.Servo(pinNum)
        self.sleepInterval = sleepInterval
        self.rotationSpeed = rotationSpeed * 10 / 90
        self.lock = _thread.allocate_lock()
        self.currentValue = 0
        self.targetValue = self.currentValue
        self.multiplier = 1
        self.lastTickMs = time.ticks_ms()
        self.needQuit = False
        self.setup()
        self.execThread = _thread.start_new_thread(self.runFunc, ())
        
    def targetValueToAngle(self, value):
        tmp = round(value * 9 + 90)
#        print('value to write: ', tmp)
        return tmp
        
    def setTargetValue(self, value):
        self.lock.acquire()

        if self.hasTransition(self.currentValue, value):
            print('Zero;')
            self.servo.writeAngle(90)
            time.sleep(0.1)
            self.servo.writeAngle(80)
            time.sleep(0.1)
            self.servo.writeAngle(90)
            time.sleep(0.1)
            self.currentValue = 0

        self.targetValue = value
        self.multiplier = 1 if self.targetValue >= self.currentValue else -1
        self.lastTickMs = time.ticks_ms()
        self.lock.release()

    def stop(self):
        self.lock.acquire()
        self.needQuit = True
        self.lock.release()

    def join(self):
        self.execThread.join()
        
    def runFunc(self):
        while True:
            self.lock.acquire()
            if True == self.needQuit:
                self.lock.release()
                return

            if self.currentValue != self.targetValue:
                (tmpTicsMs, calculatedValue) = EscControl.calculateNextStep(self.currentValue, self.rotationSpeed,
                                                                          self.multiplier, self.lastTickMs)
                valueToWrite = 0
                if self.multiplier > 0:
                    valueToWrite = calculatedValue if calculatedValue <= self.targetValue else self.targetValue
                else:
                    valueToWrite = calculatedValue if calculatedValue > self.targetValue else self.targetValue

                self.servo.writeAngle(self.targetValueToAngle(valueToWrite))
                self.currentValue = valueToWrite
                self.lastTickMs = tmpTicsMs
                
            self.lock.release()
            time.sleep(self.sleepInterval)
    
    def setup(self):
        self.servo.writeAngle(0)
        time.sleep(0.1)
        self.servo.writeAngle(180)
        time.sleep(0.1)
        self.servo.writeAngle(90)
        time.sleep(0.1)
        self.currentValue = 0
        self.targetValue = 0
        print('arm done')
        
    @staticmethod
    def hasTransition(fromValue, toValue):
        if fromValue == 0:
            return True;
        return fromValue * toValue < 0
  
    @staticmethod
    def calculateNextStep(currentValue, speedMax, multiplier, lastTickMs):
        currentTickMs = time.ticks_ms()
        timeDelta = currentTickMs - lastTickMs
        delta = speedMax * timeDelta / 1000
        return (currentTickMs, currentValue + delta * multiplier)
