# LED Light Strip Controller
This repo (currently called LEDlights) contains a controller for Neopixel LED light strips.

## Features
* Simple color commands to light up your strip
* Stackable commands that enable stylish effects
* Custom scripting language to detail creative animations and light shows
* Layers to compound multiple effects together
* Musical effects that can take input from YouTube, Spotify, or local files
* Decoupled commander and controller systems that provide for flexible interfacing

### Command Examples
Sliding rainbow
```
slide rainbow 3
```
Growing rainbow
```
colorwipe rainbow 3
```
Sliding and Growing rainbow
```
slide (colorwipe rainbow 3) 3
```
Spinning Neon lights
```
wave (gradient RED RED PURPLE BLUE BLUE) 4 150
```
Spinning Neon lights that change color
```
wave (gradient (wipe (gradient RED GREEN BLUE RED) -450) (wipe (gradient BLUE RED GREEN BLUE) -450) [2 2]) 3 150
```

### Script Example
fireworks.txt
```
let FireworkParticle = particle [(gradient RED (rgb 128 32 0) CLEAR)] (pbody 0 75 -28) 0.25 3.5 (pbody 0 83 -28) 0.35

let FadeRed = (fadeout (gradient RED CLEAR) 3)
let FadeOrange = (fadeout (gradient ORANGE CLEAR) 3)
let FadeYellow = (fadeout (gradient YELLOW CLEAR) 3)
let FadeGreen = (fadeout (gradient GREEN CLEAR) 3)
let FadeBlue = (fadeout (gradient BLUE CLEAR) 3)
let FadePurple = (fadeout (gradient PURPLE CLEAR) 3)

let SparkParticle = particle [FadeRed] (pbody -20 25 -10) 0.5 3.5 (pbody 20 15 -10) 1

let Firework = emitter FireworkParticle SparkParticle 25 3.5
let ShooterParticle = particle [PURPLE] (pbody 3)
let Shooter = emitter ShooterParticle Firework 1 7
Shooter
```
