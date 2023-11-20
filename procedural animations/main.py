import sys , pygame , math , time , os
pygame.init()

# Initialize screen
screen_size = [500, 500]
screen = pygame.display.set_mode(screen_size)
pygame.display.set_caption("Procedural Animations")
pygame.display.set_icon(pygame.transform.scale(pygame.image.load(os.path.join("Assets/Images", "icon.png")).convert(),(32,32))) 

# Global variables
game_start_time = time.time()

# Utility functions
def normalize(vector):
    mag = math.sqrt(vector[0] ** 2 + vector[1] ** 2)
    if not mag: return 0, 0
    return vector[0] / mag, vector[1] / mag

def lerp(a, b, t):  return a + (b - a) * t

def get_elbow_position(pos0, r0, pos1, r1, dt):
    d = math.sqrt((pos1[0] - pos0[0]) ** 2 + (pos1[1] - pos0[1]) ** 2)
    if (d > r0 + r1) or (d < abs(r0 - r1)) or (d == 0 and r0 == r1):    return None  # Non-intersecting, one circle within other, coincident circles
    a = (r0 ** 2 - r1 ** 2 + d ** 2) / (2 * d)
    h = math.sqrt(r0 ** 2 - a ** 2)
    return (pos0[0] + a * (pos1[0] - pos0[0]) / d + h * dt * (pos1[1] - pos0[1]) / d,   
            pos0[1] + a * (pos1[1] - pos0[1]) / d - h * dt * (pos1[0] - pos0[0]) / d,)

def rotate(origin, point, angle):
    cos_theta = math.cos(angle * (math.pi / 180))
    sin_theta = math.sin(angle * (math.pi / 180))
    return ((point[0] - origin[0]) * cos_theta - (point[1] - origin[1]) * sin_theta + origin[0],
            (point[0] - origin[0]) * sin_theta + (point[1] - origin[1]) * cos_theta + origin[1],)

# Class definitions
class Rope:
    def __init__(self, segment_lengths):
        self.node = [[screen.get_width() / 2, screen.get_height() * 0.85]]
        self.width = sum(segment_lengths)
        self.node_size = len(segment_lengths)
        self.segment_length = segment_lengths
        self.default_segment_length = segment_lengths
        self.stiffness, self.response = 0.5, 1.5

        offset = 0
        for i in range(1, len(segment_lengths)):
            offset += self.segment_length[i] + self.segment_length[i - 1]
            self.node += [[self.node[0][0], self.node[0][1] + offset]]
        self.node = list(self.node)

class Creature:
    def __init__(self, body=None, limbs=None):
        self.body = body
        self.limbs = limbs
        self.limbs_position = [[[0, 0], [0, 0], [0, 0]]] * len(self.body.node)

    def display_physic_body(self):
        pygame.draw.circle(screen, (0, 0, 0), self.body.node[0], self.body.segment_length[0], width=0)
        for i, n in enumerate(self.body.segment_length):
            n, m, r = self.body.node[i], self.body.node[max(i - 1, 0)], self.body.segment_length[i]
            if not i <= 2:  pygame.draw.line(screen, (0, 0, 0), n, m, int(r * 1.8))
            pygame.draw.circle(screen, (0, 0, 0), ((n[0] + m[0]) / 2, (n[1] + m[1]) / 2), int(r * 1.05125))

    def update_physic_body(self):
        for i in range(1, len(self.body.node)):
            N, M = self.body.node[i], self.body.node[i - 1]

            diff = (M[0] - N[0], M[1] - N[1])
            mag = math.sqrt(diff[0] ** 2 + diff[1] ** 2)
            dir = (diff[0] / mag, diff[1] / mag)

            stiffness_factor = self.body.stiffness * (math.dist(M, N) - self.body.segment_length[i] * 2)
            F = -stiffness_factor * dir[0], -stiffness_factor * dir[1]

            self.body.node[i] = (N[0] - F[0] * min(self.body.response, 2),
                                N[1] - F[1] * min(self.body.response, 2))

    def update_cosmetic_legs(self):
        angle, max_dist_to_step_position = 65, 1
        for i, info in enumerate(self.limbs):
            if info[0] <= 0 or info[0] >= len(self.body.node):  continue
            node_index, node_position, leg_length, limbs_position = (info[0],    self.body.node[info[0]],    info[2] + info[3],  self.limbs_position[i] + [])

            m = rotate(node_position, self.body.node[node_index - 1], angle * info[1])
            dir = normalize(((m[0] - node_position[0]), (m[1] - node_position[1])))

            final_step = (  node_position[0] + dir[0] * leg_length,
                            node_position[1] + dir[1] * leg_length)

            dist_to_step_position = math.dist(node_position, limbs_position[2])
            dist_to_final_step = math.dist(final_step, limbs_position[2])

            if (dist_to_step_position > leg_length * max_dist_to_step_position  or dist_to_final_step > leg_length):    limbs_position[2] = final_step
            elbow_position = get_elbow_position(node_position, info[2], limbs_position[2], info[3], info[4])

            if elbow_position:  limbs_position[1] = elbow_position
            limbs_position[0] = node_position

            self.limbs_position[i] = limbs_position + []

            pygame.draw.polygon(screen, (0, 0, 0), (limbs_position[0], limbs_position[1], limbs_position[2], limbs_position[1]),8)#Legs  
            pygame.draw.circle(screen, (255, 0, 0), limbs_position[1], 5)  # Elbow
            pygame.draw.circle(screen,(0, 0, 255), limbs_position[2], 4)  # Foot


# Initial setup
#leg Node , (-1:left or 1:right) , upper limb length , lowwer limb length , elbow angle relative(1 or -1) | ex:  [(2 , 1 , 20 , 25 , -1)]
cc = Creature(
    Rope([15, 5, 5] + [(11.25 if i < 4 else 8 - 0.5 * (i - 3)) for i in range(15)]),    [[3, 1, 23, 32, -1], [3, -1, 27, 28, 1], [6, 1, 27, 28, 1], [6, -1, 23, 32, -1]],
)

movement_speed, slithering_size, slithering_timer_multiplier = 0.125, 0.55, 0.0155

image = pygame.image.load(os.path.join("Assets/Images", "background.png")).convert_alpha()
image = pygame.transform.scale(image, (screen.get_width(), image.get_height() * (screen.get_width() / image.get_width())))

# Main loop
while True:
    elapsed_time = round((time.time() - game_start_time) * 300)
    screen.fill((240, 240, 240))

    keys = pygame.key.get_pressed()
    for event in pygame.event.get():
        if (event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE)):
            pygame.quit()
            sys.exit()

    # Breathing
    for i in range(2, int(len(cc.body.segment_length) / 2)):
        cc.body.default_segment_length[i] += math.sin(elapsed_time * 0.0075) * 0.00035

    slitheringSpeed = (math.sin(elapsed_time * slithering_timer_multiplier) * slithering_size * movement_speed)
    
    x_input, y_input = normalize((
        (keys[pygame.K_LEFT] or keys[pygame.K_a])- (keys[pygame.K_RIGHT] or keys[pygame.K_d]),
        (keys[pygame.K_UP] or keys[pygame.K_w]) - (keys[pygame.K_DOWN] or keys[pygame.K_s]))
    )
    
    cc.body.node[0][0] += (-x_input * movement_speed + (y_input * slitheringSpeed))
    cc.body.node[0][1] += (-y_input * movement_speed + (x_input * slitheringSpeed))

    screen.blit(image, (0, 50))
    cc.update_physic_body()
    cc.update_cosmetic_legs()
    cc.display_physic_body()

    pygame.display.flip()

# pyinstaller main.py --onefile