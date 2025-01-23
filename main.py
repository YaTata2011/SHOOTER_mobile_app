from kivymd.app import MDApp
from kivymd.uix.widget import MDWidget
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.metrics import sp, dp
from kivy import platform
from kivy.core.window import Window
from random import randint
from time import time
from kivymd.uix.label import MDLabel


class MainScreen(MDScreen):
    def __init__(self, *args, **kwargs):
        control = kwargs.pop('control', None) 
        super().__init__(*args, **kwargs)

        self.settingsMenu = None
        self.settingsEvent = None
        self.control = control

    def show_settings(self, *args):
        if self.settingsEvent:
            self.settingsEvent.cancel()

        if not self.settingsMenu:
            self.settingsMenu = MDDialog(
                on_dismiss=self.resumeMenu,
                text="В этой игре твоя задача сбивать вражеские корабли и уворачиватся от них",
                buttons=[
                    MDFlatButton(
                        text="CANCEL",
                        theme_text_color="Custom",
                        text_color=app.theme_cls.primary_color,
                        on_press=self.settingsStop
                    ),
                ],
            )
        self.settingsMenu.open()

    def settingsStop(self, *args):
        self.settingsMenu.dismiss()

    def resumeMenu(self, *args):
        self.settingsEvent = Clock.schedule_interval(self.control, FPS)

class Shot(MDScreen):
    ...

DIR_UP = 1
DIR_DOWN = -1

RECHARGE_DEF = 1

HP_DEF = 3

class Ship(Image):
    def __init__(self, direction = DIR_UP, recharge = RECHARGE_DEF, hp = HP_DEF, **kwargs):
        super().__init__(**kwargs)

        self.direction = direction
        self.cartridge = [] # список куль
        self.recharge = recharge
        self._lastShot = 0
        self.hp = hp
    
    def moveLeft(self):
        self.pos[0] -= dp(5)

    def moveRight(self):
        self.pos[0] += dp(5)

    def shot(self): 
        if time() - self._lastShot >= self.recharge:
            shot = Shot()
            shot.center = (self.center_x, self.top + 1)

            if self.direction == DIR_DOWN:
                shot.top = self.pos[1]

            self.cartridge.append(shot)
            self.parent.add_widget(shot)
            self._lastShot = time()

    def control(self):
       
        for bullet in self.cartridge:
            bullet.pos[1] += dp(10) * self.direction
            
            for obj in self.parent.children: 
                if bullet.collide_widget(obj) and bullet != obj:
                    self.cartridge.remove(bullet)
                    bullet.parent.remove_widget(bullet) 
                    if hasattr(obj, "hp"): obj.hp -= 1   
                     
                 

            if bullet.pos[1] >= Window.size[1] or bullet.top < 0:
                self.cartridge.remove(bullet)
                bullet.parent.remove_widget(bullet)
                


class EnemyShip(Ship):
    # frame = 0
    def control(self):
        super().control()
        self.pos[1] -= dp(3)
        self.shot()
        # if self.frame % 100 == 0:
        #     self.shot()
        # self.frame += 1



FPS = 1/60 # 60 раз у секунду
class GameScreen(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.ship = self.ids.ship
        self.enemyShips = []
        self.eventkeys = {}
        self.pauseMenu = None
        self.spawnList = {1, 3, 5, 7, 8, 9, 11}
        self.seconds = 0
        self._lastTime = time()
        
        self.game_over_label = MDLabel(
            text="",
            halign="center",
            theme_text_color="Custom",
            text_color=(1, 0, 0, 1),  # Set the text color to red
            font_style="H5",
        )
        self.game_over_label.pos = (self.center_x, self.center_y)

               

    def on_enter(self, *args):
        self.controlEvent = Clock.schedule_interval(self.control, FPS)
        return super().on_enter(*args)
    
    
    def control(self, dt):
        for key in self.eventkeys:
            if self.eventkeys[key] == True:
                if key == 'left':
                    self.ship.moveLeft()
                if key == 'right':
                    self.ship.moveRight()
                if key == 'shot':
                    self.ship.shot()
                    self.eventkeys[key] = False

        
        if self.ship.hp > 0:
            self.ids.hp_last.text = str(self.ship.hp)

        else:
            self.game_over()

        self.ship.control()

        print(str(self.ship.hp) + ' ', end='\r')


        for ship in self.enemyShips:
            ship.control()
            if ship.top <= 0 or ship.hp <= 0:
                # Видалення куль
                for bullet in ship.cartridge:
                    self.cartridge.remove(bullet)
                    bullet.parent.remove_widget(bullet)

                self.enemyShips.remove(ship)
                self.ids.front.remove_widget(ship)
        
        if time() - self._lastTime >= 1:
            self.spawn()
            self.seconds += 1
            self._lastTime = time()

    
    
    def spawn(self):
        if self.seconds in self.spawnList:

            ship = EnemyShip(DIR_DOWN)
            ship.pos = (randint(0, Window.size[0] - ship.size[0]), Window.size[1]) 
            self.enemyShips.append(ship)
            self.ids.front.add_widget(ship)

    def game_over(self):
        self.game_over_label.text = "GAME OVER"
        self.ids.interface.add_widget(self.game_over_label)
        self.controlEvent.cancel()

    def pressKey(self, key):
        self.eventkeys[key] = True

    def releaseKey(self, key):
        self.eventkeys[key] = False

    def show_menu(self):
        self.controlEvent.cancel()
        if not self.pauseMenu:
            self.pauseMenu = MDDialog(
                text="Discard draft?",
                on_dismiss=self.resumeGame,
                buttons=[
                    MDFlatButton(
                        text="CANCEL",
                        theme_text_color="Custom",
                        text_color=app.theme_cls.primary_color,
                        on_press=self.pauseStop
                    ),
                    
                ],
            )
        self.pauseMenu.open()
    def pauseStop(self, *args):
        self.pauseMenu.dismiss()

    def resumeGame(self, *args):
        self.controlEvent = Clock.schedule_interval(self.control, FPS)



class ShooterApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Purple"

        self.sm = MDScreenManager()

        game_screen = GameScreen(name='game')
        main_screen = MainScreen(name='main', control=game_screen.control)

        self.sm.add_widget(main_screen)
        self.sm.add_widget(game_screen)

        return self.sm
        
if platform != 'android':
    Window.size = (450,700)
    Window.left = 600
    Window.top = 100

app = ShooterApp()
app.run()