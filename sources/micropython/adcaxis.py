import machine

class RangeInner:
  def __init__(self, lower, upper):
    if (lower < upper):
      self.lower = lower
      self.upper = upper
    else:
      self.lower = upper
      self.upper = lower

  def enter(self, value):
    return value >= self.lower and value <= self.upper


class AdcValueMapper:

  def __init__(self, lower, middle, upper, stepCount):
    self.range = RangeInner(lower, upper)
    self.middle = middle
    self.stepCount = stepCount
    self.multipler = 1 if lower < upper else -1
    self.thresholds = []

    self.buildThresholds()

  def buildThresholds(self):
    l = -1 * self.stepCount
    lastValue = self.range.lower

    deltaL = (self.middle - self.range.lower) / (self.stepCount + 0.5)
    for i in range(1, self.stepCount + 1):
      current = round(self.range.lower + i * deltaL)
      self.thresholds.append((RangeInner(lastValue, current), l))
      lastValue = current + 1
      l = l + 1

    deltaL = (self.range.upper - self.middle) / (self.stepCount + 0.5)
    k = 0.5
    while (k < self.stepCount):
      current = round(self.middle + k * deltaL)
      # insert here
      self.thresholds.append((RangeInner(lastValue, current), l))
      k = k + 1.0
      lastValue = current + 1
      l = l + 1

    self.thresholds.append((RangeInner(lastValue, self.range.upper), l))

  def findValue(self, value):
    if value < self.range.lower:
      return self.multipler * self.stepCount * (-1)

    if value > self.range.upper:
      return self.multipler * self.stepCount

    for item in self.thresholds:
      if item[0].enter(value):
        return item[1] * self.multipler


class AdcAxis:

  def __init__(self, pinNum, lower, middle, upper, stepCount):
    self.valueMapper = AdcValueMapper(lower, middle, upper, stepCount)
    self.adc = machine.ADC(machine.Pin(pinNum))
    self.adc.atten(machine.ADC.ATTN_11DB)


  def readAndMapValue(self):
    v = self.adc.read()
    #print('value: ', v)
    return self.valueMapper.findValue(v)
