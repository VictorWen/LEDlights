import math
from color_utils import *
from effects.effects import DYNAMIC, STATIC, BaseEffect
import random


def randomBody(bodyA, bodyB):
    if bodyB is None:
        return bodyA
    return PhysicsBody(
        randfloat(bodyA.position, bodyB.position),
        randfloat(bodyA.velocity, bodyB.velocity),
        randfloat(bodyA.acceleration, bodyB.acceleration)
    )


def randfloat(a, b):
    return a + random.random() * (b - a)


class PhysicsEffect(BaseEffect):
    def __init__(self, body):
        super().__init__()
        self.body = body

    def tick(self, pixels, time_delta):
        fill_pixels(pixels, (-1, -1, -1))
        self.body.tick(time_delta)

    def clone(self):
        return PhysicsEffect(self.body)


class PhysicsBody():
    def __init__(self, pos, vel, acc):
        self.position = pos
        self.velocity = vel
        self.acceleration = acc

    def tick(self, time_delta):
        self.velocity += self.acceleration * time_delta
        self.position += self.velocity * time_delta


class ParticleEffect(PhysicsEffect):
    def __init__(self, effects, bodyA, radiusA, decayA, bodyB=None, radiusB=None, decayB=None):
        super().__init__(randomBody(bodyA, bodyB))
        self.effect = effects[random.randrange(0, len(effects))]
        self.radius = radiusA + random.random() * (radiusB -
                                                   radiusA) if radiusB is not None else radiusA
        self.decay = decayA + random.random() * (decayB -
                                                 decayA) if decayB is not None else decayA

        self.bodyA = bodyA
        self.bodyB = bodyB
        self.effects = effects
        self.radiusA = radiusA
        self.radiusB = radiusB
        self.decayA = decayA
        self.decayB = decayB

        self.lifetime = 0

    def tick(self, pixels, time_delta):
        super().tick(pixels, time_delta)

        color = clone_pixels(pixels)
        self.effect.tick(color, time_delta)

        self.lifetime += time_delta
        if self.decay > 0 and self.lifetime >= self.decay:
            fill_pixels(pixels, (-1, -1, -1))
            self.type = STATIC
            return

        N = len(pixels)
        for x in range(round(self.body.position - 3 * self.radius), round(self.body.position + 3 * self.radius) + 1):
            if 0 <= x < N:
                if self.radius > 0:
                    pixels[x] = self.gaussian_blur(
                        self.body.position - x, color)
                else:
                    pixels[x] = color[0]

    def gaussian_blur(self, dx, color):
        x2 = dx * dx
        s2 = self.radius * self.radius
        G = math.exp(- x2 / (2 * s2))

        N = len(color) - 1
        val = G * N
        return color[N - int(val)]

    def generate(self, body):
        bodyA = PhysicsBody(body.position + self.bodyA.position,
                            body.velocity + self.bodyA.velocity, self.bodyA.acceleration)
        bodyB = PhysicsBody(body.position + self.bodyB.position,
                            body.velocity + self.bodyB.velocity, self.bodyB.acceleration)

        effects = [effect.clone() for effect in self.effects]

        return ParticleEffect(
            effects,
            bodyA,
            self.radiusA,
            self.decayA,
            bodyB,
            self.radiusB,
            self.decayB
        )

    def clone(self):
        return self.generate(PhysicsBody(0, 0, 0))


class ParticleEmitter(ParticleEffect):
    def __init__(self,
                 particle: ParticleEffect,
                 emission: ParticleEffect,
                 density: float,
                 fuse: float,
                 ):
        super().__init__(
            particle.effects,
            particle.bodyA,
            particle.radiusA,
            particle.decayA,
            particle.bodyB,
            particle.radiusB,
            particle.decayB
        )
        self.particle = particle
        self.emission = emission
        self.density = density
        self.fuse = fuse

        self.is_visible = True

        self.n_triggers = 0
        self.paritlces = []

    def tick(self, pixels, time_delta):
        if self.is_visible:
            super().tick(pixels, time_delta)
            if self.type == STATIC:
                self.is_visible = False
                self.type = DYNAMIC
        else:
            fill_pixels(pixels, (-1, -1, -1))

        if (self.n_triggers + 1) * self.fuse <= self.lifetime:
            self.n_triggers += 1
            self.emit_particles()

        N = len(pixels)

        alive = []
        for particle in self.paritlces:
            colors = clone_pixels(pixels)
            particle.tick(colors, time_delta)
            for i in range(0, N):
                if colors[i] != (-1, -1, -1):
                    pixel_sum = sum(pixels[i])
                    color_sum = sum(colors[i])
                    if color_sum > pixel_sum:
                        pixels[i] = colors[i]
            if particle.type != STATIC:
                alive.append(particle)
        self.paritlces = alive

        if not self.is_visible and len(self.paritlces) == 0:
            self.type = STATIC

    def emit_particles(self):
        for _ in range(0, self.density):
            particle = self.emission.generate(self.body)
            self.paritlces.append(particle)

    def generate(self, body):
        particle = self.particle.generate(body)
        return ParticleEmitter(
            particle,
            self.emission,
            self.density,
            self.fuse
        )

    def clone(self):
        return self.generate(PhysicsBody(0, 0, 0))
