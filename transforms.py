def transform(self, x, y):  # do this so that we can either select 2D or perspective format
    #return self.transform2D(x, y)
    return self.transform_perspective(x, y)

def transform2D(self, x, y):
    return int(x), int(y)

def transform_perspective(self, x, y):  # is it possible that pythagoras thereom is used to get the perspective transformation coordinates instead?
    lin_y = (y / self.height) * self.perspective_point_y  # the new perspective height is the fraction of the y coord in respect to the perspective point of y
    if lin_y > self.perspective_point_y:  # if the value of transformed value of y is greater than the perspective y coordinate, it will just remain as the perspective point value
        lin_y = self.perspective_point_y  # new y coordinate

    diff_x = x - self.perspective_point_x
    diff_y = self.perspective_point_y - lin_y
    proportion_y = diff_y / self.perspective_point_y  # x is directly proportional to y
    factor_y = proportion_y ** 4  # this refers to the factor of spacing between the horizontal lines

    tr_x = self.perspective_point_x + diff_x * factor_y
    tr_y = self.perspective_point_y - factor_y * self.perspective_point_y

    return int(tr_x), int(tr_y)