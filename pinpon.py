from pygame import *
'''Required classes'''


#clase padre para los objetos
class GameSprite(sprite.Sprite):
   def __init__(self, player_image, player_x, player_y, player_speed, wight, height):
       super().__init__()
       self.image = transform.scale(image.load(player_image), (wight, height)) #por ejemplo. 55,55 - parámetros
       self.speed = player_speed
       self.rect = self.image.get_rect()
       self.rect.x = player_x
       self.rect.y = player_y


   def reset(self):
       window.blit(self.image, (self.rect.x, self.rect.y))


class Player(GameSprite):
    def update_l(self):
        keys= key.get_pressed()
        if keys[K_w] and self.rect.y > 5:
            self.rect.y -= self.speed
        if keys[K_s] and self.rect.y < 420:
            self.rect.y += self.speed
    def update_right(self):
        keys= key.get_pressed()
        if keys[K_UP] and self.rect.y > 5:
            self.rect.y -= self.speed
        if keys[K_DOWN] and self.rect.y < 420:
            self.rect.y += self.speed

window = display.set_mode((600, 500))
window.fill((200, 255, 255))

game = True
finish = False
clock = time.Clock()
fps = 60

racket1 = Player('racket.png', 30, 200, 4, 50, 150)
racket2 = Player('racket.png', 520, 200, 4, 50, 150)
pelota = GameSprite('pelota.png', 200, 200, 4, 50, 50)

pelota_speedx = 3
pelota_speedy = 3

font.init()
font1 = font.Font(None, 35)
lose1 = font1.render('PLAYER 1 LOSES!', True, (180, 0, 0))
lose2 = font1.render('PLAYER 2 LOSES!', True, (180, 0, 0))

while game:
    
    for e in event.get():
        if e.type == QUIT:
            game = False
    if finish != True:
        window.fill((200, 255, 255))
        
        pelota.rect.x += pelota_speedx
        pelota.rect.y += pelota_speedy
        
        if pelota.rect.y > 450:
            pelota_speedy *= -1
        if pelota.rect.y < 0:
            pelota_speedy *= -1
        
        if sprite.collide_rect(racket1, pelota):
            pelota_speedx *= -1
        if sprite.collide_rect(racket2, pelota):
            pelota_speedx *= -1
        
        if pelota.rect.x < 50:
            finish = True
            window.blit(lose1, (200, 200))
            
        if pelota.rect.x > 600:
            finish = True
            window.blit(lose2, (200, 200))
        
        racket1.update_l()
        racket2.update_right()
        racket1.reset()
        racket2.reset()
        pelota.reset()
                  
    display.update()
    clock.tick(fps)