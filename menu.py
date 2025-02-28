from kivy.uix.relativelayout import RelativeLayout


class MenuWidget(RelativeLayout):           # using a relative layout here so that the size need not be specified
    def on_touch_down(self, touch):  # need to determine if you press on the left or right of the screen
        if self.opacity == 0:       # if the menu is not visible, ignore any accidental touches on the buttob
            return False
        return super(RelativeLayout, self).on_touch_down(touch)

