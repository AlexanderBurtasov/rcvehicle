import machine
import servo
import time
import _thread

class SmoothServo:
    def __init__(self, pinNum, sleepInterval, rotationSpeed):
        self.servo = servo.Servo(pinNum)
        self.sleepInterval = sleepInterval
        self.rotationSpeed = rotationSpeed
        self.lock = _thread.allocate_lock()
        self.currentValue = 0
        self.targetValue = self.currentValue
        self.multiplier = 1
        self.lastTickMs = time.ticks_ms()
        self.needQuit = False
        self.execThread = _thread.start_new_thread(self.runFunc, ())

    def setTargetValue(self, value):
        self.lock.acquire()
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

            valueToWrite = 0
            if self.currentValue != self.targetValue:
                (tmpTicsMs, calculatedValue) = SmoothServo.calculateNextStep(self.currentValue, self.rotationSpeed,
                                                                          self.multiplier, self.lastTickMs)
                if self.multiplier > 0:
                    valueToWrite = calculatedValue if calculatedValue <= self.targetValue else self.targetValue
                else:
                    valueToWrite = calculatedValue if calculatedValue > self.targetValue else self.targetValue

                self.currentValue = round(valueToWrite)
                self.lastTickMs = tmpTicsMs
                
                self.beforeWrite(self.currentValue, valueToWrite)
                self.servo.writeAngle(int(valueToWrite))
                
            self.lock.release()
            #-+print("rotate: ", valueToWrite)
            time.sleep(self.sleepInterval)
    
    def setup(self):
        pass
    
    def beforeWrite(self, current, aim):
        pass
    
    @staticmethod
    def calculateNextStep(currentValue, speedMax, multiplier, lastTickMs):
        currentTickMs = time.ticks_ms()
        timeDelta = currentTickMs - lastTickMs
        delta = speedMax * timeDelta / 1000
        return (currentTickMs, currentValue + delta * multiplier)
