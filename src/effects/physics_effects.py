import math
from ..color_utils import *
from .effects import DYNAMIC, STATIC, BaseEffect

class PhysicsEngine(BaseEffect):
    def __init__(self, physics_effects):
        super().__init__()
        self.effects = set(physics_effects)
        self.new_effects = []
    
    def tick(self, pixels, time_delta):      
        N = len(pixels)
        colors = clone_pixels(pixels)
        self.tick_effects(colors, time_delta)

        for i in range(N):
            pixels[i] = (0, 0, 0)
        for effect in self.effects:
            left = math.floor(effect.body.position - effect.bounds)
            right = math.ceil(effect.body.position + effect.bounds)
            for x in range(left, right + 1):
                if 0 <= x < N:
                    pixels[x] = add_colors(effect.get_pixel(x), pixels[x])
          
    
    def tick_effects(self, colors, time_delta):
        dead_effects = []
        for effect in self.effects:
            effect.tick(self, colors, time_delta)
            if not effect.is_alive:
                dead_effects.append(effect)
        for effect in dead_effects:
            self.effects.remove(effect)
        for effect in self.new_effects:
            self.effects.add(effect)
        self.new_effects = []
            
    
    def add_effect(self, effect):
        self.new_effects.append(effect)
        
    
    def clone(self):
        effects = []
        for effect in self.effects:
            effects.append(effect.clone())
        return PhysicsEngine(effects)


class PhysicsBody():
    def __init__(self, pos, vel, acc):
        self.position = pos
        self.velocity = vel
        self.acceleration = acc
        self.prev_pos = pos

    def tick(self, time_delta):
        self.prev_pos = self.position
        self.position += (self.velocity + self.acceleration * time_delta  / 2) * time_delta
        self.velocity += self.acceleration * time_delta
        
    def clone(self):
        return PhysicsBody(self.position, self.velocity, self.acceleration)


class PhysicsEffect(BaseEffect):
    def __init__(self, body, collidable=False, tags=[], bounds=3):
        super().__init__()
        self.body = body
        self.is_alive = True
        self.collidable = collidable
        self.tags = set(tags)
        self.has_collision = False
        self.notify_collision = False
        self.collisions = set()
        self.notify_collisions = set()
        self.bounds = bounds

    def tick(self, engine, _, time_delta):
        if not self.is_alive:
            return
        self.body.tick(time_delta)
        if self.collidable:
            self.has_collision = self.notify_collision
            self.collisions = self.notify_collisions
            self.notify_collision = False
            self.notify_collisions = set()
            self.detect_collision(engine)
        
    def detect_collision(self, engine):        
        a = min(self.body.prev_pos, self.body.position)
        b = max(self.body.prev_pos, self.body.position)
        
        for other_effect in engine.effects:
            if other_effect is self or not other_effect.collidable:
                continue
            if a < other_effect.body.position <= b:
                self.has_collision = True
                self.collisions.add(other_effect)
                other_effect.notify_collision = True
                other_effect.notify_collisions.add(self)
        
    def get_pixel(self, index):
        return (0, 0, 0)

    def clone(self):
        tags = [tag.clone() for tag in self.tags]
        return PhysicsEffect(self.body, self.collidable, tags=tags, bounds=self.bounds)


class ParticleEffect(PhysicsEffect):
    def __init__(self, effect, pbody, radius, behaviors=[], collidable=False, tags=[]):
        super().__init__(pbody, collidable, tags, int(3 * radius + 1))
        self.effect = effect
        self.radius = radius
        
        self.colors = [(0,0,0)]
        self.N = len(self.colors) - 1
        
        self.init_behaviors = behaviors.copy()
        self.behaviors = behaviors
        self.new_behaviors = []
        
        self.brightness = 1
        
    def tick(self, engine, colors, time_delta):
        super().tick(engine, colors, time_delta)
        self.colors = resize_clone(colors, min(len(colors), math.ceil(10 * self.radius + 5)))
        self.N = len(self.colors) - 1
        self.effect.tick(self.colors, time_delta)
        
        for behavior in self.behaviors:
            behavior.tick(engine, self, time_delta)
        for new_behavior in self.new_behaviors:
            self.behaviors.append(new_behavior)
        self.new_behaviors = []
        
    def get_pixel(self, index):
        return self.gaussian_blur((self.body.position - index))
    
    def gaussian_blur(self, dx):
        if self.radius <= 0 or abs(dx) >= 3 * self.radius:
            return (0, 0, 0)
        x2 = dx * dx
        s2 = self.radius * self.radius
        G = math.exp(- x2 / (2 * s2))
        
        val = G * self.N
        if val < 1:
            return (0, 0, 0)
        return scalar_mult(self.brightness, self.colors[self.N - int(val)])

    def add_behavior(self, behavior):
        self.new_behaviors.append(behavior)

    def clone(self):
        effect = self.effect.clone()
        body = self.body.clone()
        behaviors = []
        for behavior in self.init_behaviors:
            behaviors.append(behavior.clone())
        tags = [tag.clone() for tag in self.tags]
        return ParticleEffect(effect, body, self.radius, behaviors, self.collidable, tags)
    

class ParticleBehavior():
    def __init__(self):
        pass
    
    def tick(self, engine, particle, time_delta):
        pass
    
    def clone(self):
        raise NotImplementedError()


class EmitterBehavior(ParticleBehavior):
    def __init__(self, emission, density):
        super().__init__()
        self.emission = emission
        self.density = density
        self.time_sum = 0
        self.particle_emitted = 0
    
    def tick(self, engine, particle, time_delta):
        self.time_sum += time_delta
        if self.time_sum * self.density > self.particle_emitted:
            self.emit(engine, particle)
            self.particle_emitted += 1
            
    def emit(self, engine, particle):
        emission = self.emission.clone()
        emission.body.position += particle.body.position
        emission.body.velocity += particle.body.velocity
        engine.add_effect(emission)
        
    def clone(self):
        return EmitterBehavior(self.emission.clone(), self.density)
        

class ExplosionBehavior(ParticleBehavior):
    def __init__(self, emission, density, fuse):
        super().__init__()
        self.emission = emission
        self.density = density
        self.fuse = fuse
        self.time_sum = 0
        self.explosions = 0
        
    def tick(self, engine, particle, time_delta):
        self.time_sum += time_delta
        if self.fuse == 0 or (self.time_sum / self.fuse - 1) > self.explosions:
            self.explode(engine, particle)
            self.explosions += 1
        
    def explode(self, engine, particle):
        for _ in range(self.density):
            emission = self.emission.clone()
            emission.body.position += particle.body.position
            emission.body.velocity += particle.body.velocity
            engine.add_effect(emission)
            
    def clone(self):
        return ExplosionBehavior(self.emission.clone(), self.density, self.fuse)


class CollisionBehavior(ParticleBehavior):
    def __init__(self, behaviors, once=True, tags=[]):
        super().__init__()
        self.behaviors = behaviors
        self.once = once
        self.fired = False
        self.tags = set(tags)
    
    def tick(self, engine, particle, time_delta):
        if not particle.has_collision or (self.once and self.fired and particle.is_alive):
            return
        for collider in particle.collisions:
            if (not self.once or not self.fired) and particle.is_alive and self.tags.issubset(collider.tags):
                for behavior in self.behaviors:
                    b = behavior.clone()
                    b.tick(engine, particle, 0)
                    particle.add_behavior(b)
                self.fired = True
    
    def clone(self):
        behaviors = [behavior.clone() for behavior in self.behaviors]
        tags = [tag.clone() for tag in self.tags]
        return CollisionBehavior(behaviors, self.once, tags)


class LifetimeBehavior(ParticleBehavior):
    def __init__(self, lifetime):
        self.lifetime = lifetime
        self.time_sum = 0
    
    def tick(self, engine, particle, time_delta):
        self.time_sum += time_delta
        if self.time_sum >= self.lifetime:
            particle.is_alive = False
            
    def clone(self):
        return LifetimeBehavior(self.lifetime)


class DecayBehavior(ParticleBehavior):
    def __init__(self, half_life):
        super().__init__()
        self.half_life = half_life
        self.time_sum = 0
    
    def tick(self, engine, particle, time_delta):
        self.time_sum += time_delta
        decay = math.pow(0.5, self.time_sum / self.half_life)
        particle.brightness = decay
    
    def clone(self):
        return DecayBehavior(self.half_life)
    
    
class Tag:
    def __init__(self, string):
        self.string = string
        
    def __repr__(self):
        return self.string
    
    def __eq__(self, other):
        return self.string == other
    
    def __ne__(self, other):
        return self.string != other
    
    def __hash__(self):
        return self.string.__hash__() 
        
    def clone(self):
        return Tag(self.string)
    

class CountingTag(Tag):
    def __init__(self, start=0, prefix=""):
        super().__init__(f"{prefix}{start}")
        self.start = start
        
    def __repr__(self):
        return self.string
        
    def clone(self):
        self.start += 1
        return CountingTag(self.start)