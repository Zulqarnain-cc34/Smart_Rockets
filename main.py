import sys
import pygame
# import time
import numpy as np
import random
import math
# import time
# from scipy.ndimage.interpolation import rotate
from utils import mapRange
from functools import reduce

# screen
WIDTH, HEIGHT = (1200, 800)
TARGET = np.array([WIDTH / 2, 300  + HEIGHT / 2])
LIFESPAN = 1300

# Color
BLACK = (0, 0, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)

# MAX_DIST = 0

class Population(object):
    """ Creates a array of Rockets and Performs Functions as a whole"""
    def __init__(self):

        self.rockets = [] # Array to store rocket objects
        self.pop_max = 25  # Maximum Population size

        self.mating_pool = [] # to store copies of rocket objects for selection

        # Creates given amount of objects and stores it in an array
        for _ in range(self.pop_max):
            self.rockets.append(Rocket())

    def run(self, win, counter):
        """ Updates our Population object params and shows it on screen """
        for i in range(self.pop_max):
            self.rockets[i].update(win, counter)

    def evaluate(self):
        """ Evalutes our Population based on some fitness value and creates a mating poll based on them """
        max_fitness = 0
        sum_fitness = 0

        for i in range(self.pop_max):
            self.rockets[i].calcfitness()
            if self.rockets[i].fitness > max_fitness:
                max_fitness = self.rockets[i].fitness
                sum_fitness += self.rockets[i].fitness

        # print("Max_fitness: ", max_fitness)
        # THe more close to 1 the better
        print("Average Fitness: ", sum_fitness / max_fitness)

        for i in range(self.pop_max):
            self.rockets[i].fitness /= max_fitness

        # Empties the mating pool before putting new population in it
        self.mating_pool = []

        for i in range(self.pop_max):
            n = math.floor(self.rockets[i].fitness * 100)
            for _ in range(n):
                self.mating_pool.append(self.rockets[i])
        print("Mating Pool: ", len(self.mating_pool))

    def natural_selection(self):
        """ Selects two fit members of Population and performs crossover and mutation on them, 
            then makes the new population based on the new created member """
        new_rockets = []
        for _ in range(len(self.rockets)):
            parentA = np.random.choice(self.mating_pool).dna
            parentB = np.random.choice(self.mating_pool).dna
            child = parentA.crossover(parentB)
            child.mutation()
            new_rockets.append(Rocket(child))
        self.rockets = new_rockets


class DNA(object):
    def __init__(self, genes=[], num_thrusters=1):
        self.mag = 0.1  # Force scaling factor
        self.num_thrusters = num_thrusters

        # If genes is not provided initializes a random value for it, otherwise takes it as a param
        if genes != []:
            self.genes = genes
        else:
            # to minimize the starting force vectors to small values
            self.genes = np.random.rand(LIFESPAN, self.num_thrusters) * self.mag

    def crossover(self, partner):
        """ Combines two members and makes an offspring of both """
        newgenes = np.zeros((len(self.genes), 4))

        mid = np.random.randint(len(self.genes))
        for i in range(len(self.genes)):
            if i > mid:
                newgenes[i] = self.genes[i]
            else:
                newgenes[i] = partner.genes[i]

        # to minimize the new force vectors to small values
        # newgenes = newgenes * self.mag

        return DNA(newgenes, self.num_thrusters)

    def mutation(self):
        """ Random Chance of the new member having different properties than the parents """
        for i in range(len(self.genes)):
            # if random number less than 0.01, new gene is then random vector
            if random.random() < 0.01:

                mutated_gene = np.random.randn(self.num_thrusters)
                self.genes[i] = mutated_gene


class Rocket():
    count = 0

    def __init__(self, dna=None, theta=20):
        # Accelartion, Velocity and Position Vectors
        self.acc = np.zeros((1, 2))[0]  # Starting Accwlartion 
        self.vel = np.zeros((1, 2))[0]  # Starting velocity

        self.rocket_width = 30
        self.rocket_height = 30

        self.pos = np.array([WIDTH / 2,  100])    # Starting position
        self.distance = 0

        self.theta_dot = 0  # Starting angular velocity
        self.fitness = 0    # Starting fitness value

        self.color = WHITE
        self.theta = np.radians(theta)  # Starting Angle in Radians
        self.mag = 0.005                # Rotation Scaling Factor

        self.booster_size = 20          # Scaling Factor of Booster image

        self.image = pygame.image.load("./assets/rocket.png")
        self.image = pygame.transform.scale(self.image, (self.rocket_height, self.rocket_height))

        # self.booster = pygame.image.load("./assets/loud.png")
        # self.booster = pygame.transform.scale(self.booster, (self.booster_size, self.booster_size))

        self.completed = False
        self.crashed = False
        self.fitness_mag = 0.2
        # self.distance = 

        if dna is not None:
            self.dna = dna
        else:
            self.dna = DNA(num_thrusters=4)

        # FIX: Convert Trusters into an array
        self.TRUSTER_1 = np.array([self.rocket_width / 4, -self.rocket_height / 2])
        self.TRUSTER_2 = np.array([self.rocket_width / 2, -self.rocket_height / 2])
        self.TRUSTER_3 = np.array([- self.rocket_width / 4, -self.rocket_height / 2])
        self.TRUSTER_4 = np.array([- self.rocket_width / 2, self.rocket_height / 2])

        self.num_thrusters = 4

        self.thrusters = [self.TRUSTER_1, self.TRUSTER_2, self.TRUSTER_3, self.TRUSTER_4]
        self.forces = self.dna.genes

    def global_coords(self, x, y):
        """ Convert local coords to global coords """
        return self.pos + np.array([x, y])

    def show(self, win):
        """ Draws the rocket object and its booster points """
        self.draw_img(win, self.image, self.pos[0], HEIGHT - self.pos[1], np.rad2deg(self.theta))

        # for i in range(self.num_thrusters):
        #     self.draw_boosters(win, self.booster, self.thrusters[i][0], self.thrusters[i][1])

    def draw_img(self, screen, image, x, y, angle):
        """ Rotates the image for rocket by the given angle and draws the rotated image"""
        rotated_image = pygame.transform.rotate(image, angle)
        screen.blit(rotated_image, rotated_image.get_rect(center=image.get_rect(topleft=(x, y)).center).topleft)

    def draw_boosters(self, screen, image, x, y):
        """ Rotates the boosters for rocket by the pos and draws the rotated boosters"""
        # screen.blit(rotated_image, rotated_image.get_rect(center=image.get_rect(topleft=(x, y)).center).topleft)
        global_booster_coords = self.global_coords(x, y)
        screen.blit(image, image.get_rect(center=(global_booster_coords[0], global_booster_coords[1])))

    def torque(self, r, force):
        """ Calculates the Torque of the given Force """
        return r[0] * force

    def calcfitness(self):
        """ calculates the distance between target and our current position and geives a fitness value """
        distance = self.dist(self.pos, TARGET)

        self.fitness = mapRange(distance, 0, WIDTH, WIDTH, 0)

        if self.completed:
            self.fitness *= 10

        if self.crashed:
            self.fitness /= 10

    def collision(self):
        """ Detects collision with the edges of the screen and stops the rocket """
        # Rocket has hit left or right of window
        if (self.pos[0] + self.rocket_width > WIDTH or self.pos[0] < 0):
            self.crashed = True

        # Rocket has hit top or bottom of window
        if (self.pos[1] + self.rocket_height > HEIGHT or self.pos[1] < 0):
            self.crashed = True

    def dist(self, a, b):
        """ Euclidean Distance Formula """
        return math.sqrt((b[1]- a[1]) ** 2 + (b[0] - a[0]) ** 2) * self.fitness_mag

    def sum_of_all_torques(self, forces):
        """  Calculates the Torque from all the force Vectors and calculates it sum"""
        sum = self.torque(self.TRUSTER_1, forces[0]) + self.torque(self.TRUSTER_2, forces[1]) + self.torque(self.TRUSTER_3, forces[2]) + self.torque(self.TRUSTER_4, forces[3])

        return self.mag * np.isscalar(sum)

    def sum_of_all_forces(self, force, theta):
        """  Calculates the sum of all the force Vectors"""
        sum_of_forces = np.array(reduce(lambda a, b: a + b, force))

        global_forces = np.array([-sum_of_forces * np.sin(theta), sum_of_forces * np.cos(theta)])
        return global_forces

    def calculate(self, canonical_forces, initial_pos, initial_vel):
        self.acc = canonical_forces * 0.01
        final_vel = self.acc + initial_vel

        final_pos = initial_pos + (final_vel + initial_vel) / 2
        return final_vel, final_pos

    def update(self, win, i):
        """ Calculates the new velocity, position, angular velocity and theta based on the ΣF and Στ 
            , updates the new Forces and draws it on screen """

        dis = self.dist(TARGET, self.pos)

        if dis < 10:
            self.completed = True
            self.pos = TARGET

        # Rocket has hit left or right of window
        if (self.pos[0] + self.rocket_width > WIDTH or self.pos[0] < 0):
            self.crashed = True

        # Rocket has hit top or bottom of window
        if (self.pos[1] + self.rocket_height > HEIGHT or self.pos[1] < 0):
            self.crashed = True


        if not self.completed and not self.crashed:
            self.theta_dot, self.theta = self.calculate(self.sum_of_all_torques(self.forces[i]), self.theta, self.theta_dot)
            #FIX: We need to first calculate rotational matric by calculating theta so theta is theta is calculated first before finding sum of all forces
            self.vel, self.pos = self.calculate(self.sum_of_all_forces(self.forces[i], self.theta), self.pos, self.vel)

        self.show(win)

# updates the screen with every main game loop
def redrawwindow(win, rocket, counter):
    win.fill(BLACK)
    # win.blit(BG_IMG,(0,0))
    draw_circle(win)
    rocket.run(win, counter)
    pygame.display.update()


def draw_circle(win):
    pygame.draw.circle(win, RED, (TARGET[0], HEIGHT - TARGET[1]), 5)


def Mainloop():
    LIFE = 0
    popl = Population()
    pygame.init()
    win = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Smart Rockets Game")
    clock = pygame.time.Clock()

    count = 0
    Fps = 200

    run = True
    while run:
        clock.tick(Fps)
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == keys[pygame.QUIT] or keys[pygame.K_ESCAPE]:
                run = False
                sys.exit()

        # popl.run(win, LIFE)
        LIFE += 1
        if LIFE == LIFESPAN:
            LIFE = 0

        count += 1
        if count == LIFESPAN:
            popl.evaluate()
            popl.natural_selection()
            count = 0

        # time.sleep(0.01)
        redrawwindow(win, popl, LIFE)
    pygame.QUIT
    quit()


Mainloop()
