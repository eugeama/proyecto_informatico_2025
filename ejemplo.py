import pygame

pygame.init()

screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Text Input Example")

font = pygame.font.Font(None, 32)
text_color = (255, 255, 255)  # White
input_box_rect = pygame.Rect(200, 200, 140, 32)
active_color = (255, 0, 0)  # Red
inactive_color = (100, 100, 100) # Gray
current_color = inactive_color

user_text = ''
active = False

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if input_box_rect.collidepoint(event.pos):
                active = not active
            else:
                active = False
            current_color = active_color if active else inactive_color
        if event.type == pygame.KEYDOWN:
            if active:
                if event.key == pygame.K_BACKSPACE:
                    user_text = user_text[:-1]
                elif event.key == pygame.K_RETURN:
                    print(f"User entered: {user_text}")
                    user_text = '' # Clear after enter
                else:
                    user_text += event.unicode

    screen.fill((0, 0, 0)) # Black background

    # Render the text
    text_surface = font.render(user_text, True, text_color)
    screen.blit(text_surface, (input_box_rect.x + 5, input_box_rect.y + 5))

    # Draw the input box
    pygame.draw.rect(screen, current_color, input_box_rect, 2)

    pygame.display.flip()

pygame.quit()