# -*- coding: utf-8 -*-    
from cv2 import cv2

from captcha.solveCaptcha import solveCaptcha

from os import listdir
from src.logger import logger, loggerMapClicked
from random import random
from pyclick import HumanClicker


import numpy as np
import mss
import pyautogui
import time
import sys

import yaml


cat = """

>>---> Press ctrl + c to kill the bot.

>>---> Some configs can be fount in the config.yaml file."""


print(cat)


if __name__ == '__main__':
    stream = open("config.yaml", 'r')
    c = yaml.safe_load(stream)

ct = c['threshold']
ch = c['home']

hc = HumanClicker()


if not ch['enable']:
    print('>>---> Home feature not enabled')
print('\n')

pyautogui.PAUSE = c['time_intervals']['interval_between_moviments']

pyautogui.FAILSAFE = False
hero_clicks = 0
login_attempts = 0
last_log_is_progress = False


def solveCaptchaPuzzle(message):
    try:
        logger('Looking for captcha for %s' % message)
        if clickBtn(images['robot'], name='solvingCaptcha', timeout = 10):
            logger('Solving captcha for %s' % message )
            solveCaptcha()
        else:
            logger('Captcha popup not found. Proceeding...')
            return
    except:
        logger('Error while solving captcha')


def addRandomness(n, randomn_factor_size=None):
    if randomn_factor_size is None:
        randomness_percentage = 0.1
        randomn_factor_size = randomness_percentage * n

    random_factor = 2 * random() * randomn_factor_size
    if random_factor > 5:
        random_factor = 5
    without_average_random_factor = n - randomn_factor_size
    randomized_n = int(without_average_random_factor + random_factor)
    return int(randomized_n)

def moveToWithRandomness(x,y,t):
    hc.move((addRandomness(x,10),addRandomness(y,10)),t+random()/2)



def remove_suffix(input_string, suffix):
    if suffix and input_string.endswith(suffix):
        return input_string[:-len(suffix)]
    return input_string

def load_images():
    file_names = listdir('./targets/')
    targets = {}
    for file in file_names:
        path = 'targets/' + file
        targets[remove_suffix(file, '.png')] = cv2.imread(path)

    return targets

images = load_images()

def loadHeroesToSendHome():
    file_names = listdir('./targets/heroes-to-send-home')
    heroes = []
    for file in file_names:
        path = './targets/heroes-to-send-home/' + file
        heroes.append(cv2.imread(path))

    print('>>---> %d heroes that should be sent home loaded' % len(heroes))
    return heroes

if ch['enable']:
    home_heroes = loadHeroesToSendHome()


full_stamina = cv2.imread('targets/full-stamina.png')
robot = cv2.imread('targets/robot.png')
slider = cv2.imread('targets/slider.png')



def show(rectangles, img = None):

    if img is None:
        with mss.mss() as sct:
            monitor = sct.monitors[0]
            img = np.array(sct.grab(monitor))

    for (x, y, w, h) in rectangles:
        cv2.rectangle(img, (x, y), (x + w, y + h), (255,255,255,255), 2)

    cv2.imshow('img',img)
    cv2.waitKey(0)



def clickBtn(img,name=None, timeout=3, threshold = ct['default']):
    logger(None, progress_indicator=True)
    if not name is None:
        pass
    start = time.time()
    clicked = False
    while(not clicked):
        matches = positions(img, threshold=threshold)
        if(len(matches)==0):
            hast_timed_out = time.time()-start > timeout
            if(hast_timed_out):
                if not name is None:
                    pass
                return False
            continue

        x,y,w,h = matches[0]
        pos_click_x = x+w/2
        pos_click_y = y+h/2
        moveToWithRandomness(pos_click_x,pos_click_y,1)
        pyautogui.click()
        return True

def printSreen():
    with mss.mss() as sct:
        monitor = sct.monitors[0]
        sct_img = np.array(sct.grab(monitor))
        return sct_img[:,:,:3]

def positions(target, threshold=ct['default'],img = None):
    if img is None:
        img = printSreen()
    result = cv2.matchTemplate(img,target,cv2.TM_CCOEFF_NORMED)
    w = target.shape[1]
    h = target.shape[0]

    yloc, xloc = np.where(result >= threshold)


    rectangles = []
    for (x, y) in zip(xloc, yloc):
        rectangles.append([int(x), int(y), int(w), int(h)])
        rectangles.append([int(x), int(y), int(w), int(h)])

    rectangles, weights = cv2.groupRectangles(rectangles, 1, 0.2)
    return rectangles

def scroll():

    commoms = positions(images['commom-text'], threshold = ct['commom'])
    if (len(commoms) == 0):
        return
    x,y,w,h = commoms[len(commoms)-1]
#
    moveToWithRandomness(x,y,1)

    if not c['use_click_and_drag_instead_of_scroll']:
        pyautogui.scroll(-c['scroll_size'])
    else:
        pyautogui.dragRel(0,-c['click_and_drag_amount'],duration=1, button='left')


def clickButtons():
    buttons = positions(images['go-work'], threshold=ct['go_to_work_btn'])
    for (x, y, w, h) in buttons:
        moveToWithRandomness(x+(w/2),y+(h/2),1)
        pyautogui.click()
        global hero_clicks
        hero_clicks = hero_clicks + 1
    return len(buttons)

def isHome(hero, buttons):
    y = hero[1]

    for (_,button_y,_,button_h) in buttons:
        isBelow = y < (button_y + button_h)
        isAbove = y > (button_y - button_h)
        if isBelow and isAbove:
            return False
    return True

def isWorking(bar, buttons):
    y = bar[1]

    for (_,button_y,_,button_h) in buttons:
        isBelow = y < (button_y + button_h)
        isAbove = y > (button_y - button_h)
        if isBelow and isAbove:
            return False
    return True

def clickGreenBarButtons():
    offset = 130

    green_bars = positions(images['green-bar'], threshold=ct['green_bar'])
    logger('%d green bars detected' % len(green_bars))
    buttons = positions(images['go-work'], threshold=ct['go_to_work_btn'])
    logger('%d buttons detected' % len(buttons))


    not_working_green_bars = []
    for bar in green_bars:
        if not isWorking(bar, buttons):
            not_working_green_bars.append(bar)
    if len(not_working_green_bars) > 0:
        logger('%d buttons with green bar detected' % len(not_working_green_bars))
        logger('Clicking in %d heroes' % len(not_working_green_bars))

    for (x, y, w, h) in not_working_green_bars:
        moveToWithRandomness(x+offset+(w/2),y+(h/2),1)
        pyautogui.click()
        global hero_clicks
        hero_clicks = hero_clicks + 1
    return len(not_working_green_bars)

def clickFullBarButtons():
    offset = 100
    full_bars = positions(images['full-stamina'], threshold=ct['default'])
    buttons = positions(images['go-work'], threshold=ct['go_to_work_btn'])

    not_working_full_bars = []
    for bar in full_bars:
        if not isWorking(bar, buttons):
            not_working_full_bars.append(bar)

    if len(not_working_full_bars) > 0:
        logger('Clicking in %d heroes' % len(not_working_full_bars))

    for (x, y, w, h) in not_working_full_bars:
        moveToWithRandomness(x+offset+(w/2),y+(h/2),1)
        pyautogui.click()
        global hero_clicks
        hero_clicks = hero_clicks + 1

    return len(not_working_full_bars)

def goToHeroes():
    checkHeroScreenStatTimeout = 60

    if clickBtn(images['go-back-arrow']):
        global login_attempts
        login_attempts = 0

    if clickBtn(images['hero-icon'], timeout = 5):
        solveCaptchaPuzzle('Go to Heroes')
        start = time.time()
        present = False
        while(not present):
            matches = positions(images['commom-text'])
            if(len(matches)==0):
                hast_timed_out = time.time()-start > checkHeroScreenStatTimeout
                if(hast_timed_out):
                    present = True
                    logger('Heroes screen did not load after %d seconds' % checkHeroScreenStatTimeout)
                    logger('Refreshing the heroes screen...')
                    login_attempts = 4
                else:
                    logger('Waiting for heroes screen to load...' )
                    time.sleep(1)
            else:
                logger('Heroes screen loading is finished')
                return True
    else:
        return False


def goToGame():
    clickBtn(images['x'])
    clickBtn(images['treasure-hunt-icon'])

def refreshHeroesPositions():
    if(clickBtn(images['go-back-arrow'], timeout = 5)):
        logger('Refreshing Heroes Positions.')
        clickBtn(images['treasure-hunt-icon'])
    else:
        logger('Skipping refreshing Heroes Positions.')

def login():
    global login_attempts
    attemptsWait = 5
    retryNumber=3

    logger('Checking if game has disconnected')

    if login_attempts > 3:
        login_attempts = 0
        logger('Too many login attempts. Refreshing the page then waiting %d seconds...' % attemptsWait)
        pyautogui.hotkey('ctrl','f5')
        time.sleep(attemptsWait)
        
        nbRetry = 0
        while(nbRetry < retryNumber):
            if(clickBtn(images['unity-loading'], timeout=30)):
                logger('Unity loading screen not found. Proceeding...')
                nbRetry = retryNumber
            else:
                nbRetry = nbRetry + 1
                logger('Unity loading screen is stuck. Refreshing the page')
                pyautogui.hotkey('ctrl','f5')
        return
   
    connectWallet()

    loginError()

    if clickBtn(images['progress-bar'], name='progressBar', timeout = 20):
        logger('Progress bar screen is stuck. Refreshing the page')
        pyautogui.hotkey('ctrl','f5')
        time.sleep(attemptsWait)
        return

def connectWallet():
    global login_attempts
    
    if clickBtn(images['select-wallet-2'], name='sign button', timeout=5):
        logger('Confirm connect wallet button detected')

    loginError()
   
    if clickBtn(images['connect-wallet'], name='connectWalletBtn', timeout = 10):
        solveCaptchaPuzzle('Connect to Wallet')
        login_attempts = login_attempts + 1
        logger('Connect wallet button detected')
    if clickBtn(images['select-wallet-2'], name='sign button', timeout=15):
        logger('Confirm connect wallet button detected')
        if clickBtn(images['treasure-hunt-icon'], name='teasureHunt', timeout = 60):
            logger('Login successfully!')
            login_attempts = 0
            return

def loginError():
    if clickBtn(images['ok'], name='okBtn', timeout=5):
        logger('Error pop-up detected')
        connectWallet()

def sendHeroesHome():
    if not ch['enable']:
        return
    heroes_positions = []
    for hero in home_heroes:
        hero_positions = positions(hero, threshold=ch['hero_threshold'])
        if not len (hero_positions) == 0:
            hero_position = hero_positions[0]
            heroes_positions.append(hero_position)

    n = len(heroes_positions)
    if n == 0:
        print('No heroes that should be sent home found.')
        return
    print(' %d heroes that should be sent home found' % n)
    go_home_buttons = positions(images['send-home'], threshold=ch['home_button_threshold'])
    go_work_buttons = positions(images['go-work'], threshold=ct['go_to_work_btn'])

    for position in heroes_positions:
        if not isHome(position,go_home_buttons):
            print(isWorking(position, go_work_buttons))
            if(not isWorking(position, go_work_buttons)):
                print ('hero not working, sending him home')
                moveToWithRandomness(go_home_buttons[0][0]+go_home_buttons[0][2]/2,position[1]+position[3]/2,1)
                pyautogui.click()
            else:
                print ('hero working, not sending him home(no dark work button)')
        else:
            print('hero already home, or home full(no dark home button)')



def refreshHeroes():
    if(goToHeroes()):

        logger('Sending heroes to work.')

        if c['select_heroes_mode'] == "full":
            logger('Sending heroes with full stamina bar to work', 'green')
        elif c['select_heroes_mode'] == "green":
            logger('Sending heroes with green stamina bar to work', 'green')
        else:
            logger('Sending all heroes to work', 'green')

        buttonsClicked = 1
        empty_scrolls_attempts = c['scroll_attemps']

        while(empty_scrolls_attempts >0):
            if c['select_heroes_mode'] == 'full':
                buttonsClicked = clickFullBarButtons()
            elif c['select_heroes_mode'] == 'green':
                buttonsClicked = clickGreenBarButtons()
            else:
                buttonsClicked = clickButtons()

            sendHeroesHome()

            if buttonsClicked == 0:
                empty_scrolls_attempts = empty_scrolls_attempts - 1
            scroll()
            time.sleep(2)
        logger('{} heroes sent to work'.format(hero_clicks))
        goToGame()
    else:
        logger('Skipping sending heroes to work')

def main():
    time.sleep(5)
    t = c['time_intervals']

    last = {
    "login" : 0,
    "heroes" : 0,
    "new_map" : 0,
    "check_for_captcha" : 0,
    "refresh_heroes" : 0
    }

    while True:
        now = time.time()

        if now - last["check_for_captcha"] > addRandomness(t['check_for_captcha'] * 60):
            last["check_for_captcha"] = now
            solveCaptchaPuzzle('Loop')

        if now - last["login"] > addRandomness(t['check_for_login'] * 60):
            sys.stdout.flush()
            last["login"] = now
            login()

        if now - last["heroes"] > addRandomness(t['send_heroes_for_work'] * 60):
            last["heroes"] = now
            refreshHeroes()

        if now - last["new_map"] > t['check_for_new_map_button']:
            last["new_map"] = now

            if clickBtn(images['new-map']):
                loggerMapClicked()


        if now - last["refresh_heroes"] > addRandomness( t['refresh_heroes_positions'] * 60):
            last["refresh_heroes"] = now
            refreshHeroesPositions()

        logger(None, progress_indicator=True)

        sys.stdout.flush()

        time.sleep(1)



main()