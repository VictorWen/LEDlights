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
            pixels[i] = (0, 0, 0, 0)
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
    

class CollisionEvent:
    def __init__(self, particleA, particleB, collision_time):
        self.particle = particleA
        self.other = particleB
        self.collision_time = collision_time
        self._calculate_collision_bodies()
        
    def _calculate_collision_bodies(self):
        bodyA = self.particle.body
        bodyB = self.other.body
        
        t = self.collision_time
        
        pos1 = bodyA.prev_pos
        vel1 = bodyA.prev_vel
        acc1 = bodyA.acceleration
        
        pos2 = bodyB.prev_pos
        vel2 = bodyB.prev_vel
        acc2 = bodyB.acceleration
            
        pos = pos1 + (vel1 + acc1 * t / 2) * t 
            
        u1 = vel1 + acc1 * t
        u2 = vel2 + acc2 * t
        
        self.bodyA = PhysicsBody(pos, u1, acc1, bodyA.mass)
        self.bodyB = PhysicsBody(pos, u2, acc2, bodyB.mass)


class PhysicsBody:
    def __init__(self, pos, vel, acc, mass=1):
        self.position = pos
        self.velocity = vel
        self.acceleration = acc
        self.prev_pos = pos
        self.prev_vel = vel
        self.mass = mass
        
    def __repr__(self):
        return f"(pbody {self.position} {self.velocity} {self.acceleration} {self.mass})"

    def tick(self, time_delta):
        self.prev_pos = self.position
        self.prev_vel = self.velocity
        self.position += (self.velocity + self.acceleration * time_delta  / 2) * time_delta
        self.velocity += self.acceleration * time_delta
        
    def clone(self):
        return PhysicsBody(self.position, self.velocity, self.acceleration, self.mass)


class PhysicsEffect(BaseEffect):
    def __init__(self, body, collidable=False, tags=[], bounds=3):
        super().__init__()
        self.body = body
        self.is_alive = True
        self.collidable = collidable
        self.tags = set(tags)
        self.has_collision = False
        self.notify_collision = False
        self.collisions = {}
        self.notify_collisions = {}
        self.bounds = bounds

    def tick(self, engine, _, time_delta):
        if not self.is_alive:
            return
        self.body.tick(time_delta)
        if self.collidable:
            self.has_collision = self.notify_collision
            self.collisions = self.notify_collisions
            self.notify_collision = False
            self.notify_collisions = {}
            self.detect_collision(engine, time_delta)
        
    def detect_collision(self, engine, time_delta):        
        a = min(self.body.prev_pos, self.body.position)
        b = max(self.body.prev_pos, self.body.position)
        
        for other_effect in engine.effects:
            if other_effect is self or not other_effect.collidable or id(other_effect) in self.collisions:
                continue
            if a < other_effect.body.position <= b:
                collision_time = self.calculate_collision_time(other_effect)
                if collision_time < 0 or collision_time > time_delta:
                    continue
                
                self.has_collision = True
                self.collisions[id(other_effect)] = CollisionEvent(self, other_effect, collision_time)
                other_effect.notify_collision = True
                other_effect.notify_collisions[id(self)] = CollisionEvent(other_effect, self, collision_time)
                
    
    def calculate_collision_time(self, other):
        delta_pos = other.body.prev_pos - self.body.prev_pos
        delta_vel = other.body.prev_vel - self.body.prev_vel
        delta_acc = other.body.acceleration - self.body.acceleration
        
        if delta_acc != 0:
            discrim = delta_vel * delta_vel - 2 * delta_acc * delta_pos
            if discrim < 0:
                return -1
            sqrt_discrim = math.sqrt(discrim)
            
            delta_t = (-delta_vel - sqrt_discrim) / delta_acc
            if delta_t < 0:
                delta_t = (-delta_vel + sqrt_discrim) / delta_acc
        elif delta_vel != 0:
            delta_t = -delta_pos / delta_vel           
        else:
            return -1
        
        if delta_t < 0:
            return -1
        return delta_t
                
        
    def get_pixel(self, index):
        return (0, 0, 0, 0)

    def clone(self):
        tags = [tag.clone() for tag in self.tags]
        return PhysicsEffect(self.body, self.collidable, tags=tags, bounds=self.bounds)


class ParticleEffect(PhysicsEffect):
    def __init__(self, effect, pbody, radius, behaviors=[], collidable=False, tags=[]):
        super().__init__(pbody, collidable, tags, int(3 * radius + 1))
        self.effect = effect
        self.radius = radius
        
        self.colors = [(0,0,0,0)]
        self.N = len(self.colors) - 1
        
        self.init_behaviors = behaviors.copy()
        self.behaviors = behaviors
        self.new_behaviors = []
        
        self.brightness = 1
        
    def tick(self, engine, colors, time_delta):
        super().tick(engine, colors, time_delta)
        if self.N < 5 or self.effect.type == DYNAMIC:
            self.colors = resize_clone(colors, min(len(colors), math.ceil(10 * self.radius + 5)))
            self.N = len(self.colors) - 1
            self.effect.tick(self.colors, time_delta)
        
        self.tick_behaviors(engine, time_delta)
        
    def tick_behaviors(self, engine, time_delta):
        i = 0
        while i < len(self.behaviors):
            behavior = self.behaviors[i]
            behavior.tick(engine, self, time_delta)
            if not behavior.is_alive:
                self.behaviors.pop(i)
            else: 
                i += 1
        for new_behavior in self.new_behaviors:
            self.behaviors.append(new_behavior)
        self.new_behaviors = []
        
    def get_pixel(self, index):
        return self.gaussian_blur((self.body.position - index))
    
    def gaussian_blur(self, dx):
        if self.radius <= 0 or abs(dx) >= 3 * self.radius:
            return (0, 0, 0, 0)
        x2 = dx * dx
        s2 = self.radius * self.radius
        G = math.exp(- x2 / (2 * s2))
        
        val = G * self.N
        if val < 1:
            return (0, 0, 0, 0)
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
        self.is_alive = True
    
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
        for collider, collision in particle.collisions.items():
            if (not self.once or not self.fired) and particle.is_alive and self.tags.issubset(collision.other.tags):
                for behavior in self.behaviors:
                    b = behavior.clone()
                    b.tick(engine, particle, time_delta)
                    particle.add_behavior(b)
                self.fired = True
        if self.once and self.fired:
            self.is_alive = False
    
    def clone(self):
        behaviors = [behavior.clone() for behavior in self.behaviors]
        tags = [tag.clone() for tag in self.tags]
        return CollisionBehavior(behaviors, self.once, tags)
    

class RigidColliderBehavior(ParticleBehavior):
    def __init__(self, coeff_restitution, tags=[]):
        super().__init__()
        self.coeff_res = coeff_restitution
        self.tags = set(tags)
        
    def tick(self, engine, particle, time_delta):
        if not particle.has_collision:
            return
        
        min_time = None
        for collider, collision in particle.collisions.items():
            if self.tags.issubset(collision.other.tags) and (min_time is None or collision.collision_time < min_time.collision_time):
                min_time = collision
        self.calculate_post_collision(particle, min_time, time_delta)
                
    def calculate_post_collision(self, particle, collision, time_delta):
        if collision is None:
            return
        m1 = collision.bodyA.mass
        m2 = collision.bodyB.mass
        mass_sum = m1 + m2
        if mass_sum <= 0:
            return
        
        remaining_time_delta = time_delta - collision.collision_time
        
        pos = collision.bodyA.prev_pos
        u1 = collision.bodyA.prev_vel
        u2 = collision.bodyB.prev_vel
        u_d = u2 - u1
        p1 = m1 * u1
        p2 = m2 * u2
        
        vel = (self.coeff_res * m2 * u_d + p1 + p2) / mass_sum
        
        particle.body.position = pos
        particle.body.velocity = vel
        particle.body.tick(remaining_time_delta)
        
    def clone(self):
        return RigidColliderBehavior(self.coeff_res, [tag.clone() for tag in self.tags])


class LifetimeBehavior(ParticleBehavior):
    def __init__(self, lifetime):
        super().__init__()
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
    
    
class ImpluseBehavior(ParticleBehavior):
    def __init__(self, constant, momentum_coef):
        super().__init__()
        self.constant = constant
        self.coef = momentum_coef
        self.fired = False
    
    def tick(self, engine, particle, time_delta):
        if self.fired:
            return
        delta_v = 0
        delta_v += self.constant + self.coef * particle.body.velocity
        
        particle.body.velocity += delta_v
        particle.body.position += delta_v * time_delta
        self.fired = True
        self.is_alive = False
        
    def clone(self):
        return ImpluseBehavior(self.constant, self.coef)
    
    
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
        super().__init__(f"{prefix}-{start}")
        self.start = start
        self.prefix = prefix
        self.count = start
        
    def __repr__(self):
        return self.string
        
    def clone(self):
        self.count += 1
        return CountingTag(self.count, self.prefix)