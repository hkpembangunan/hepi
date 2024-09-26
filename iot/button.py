import gpiozero  # We are using GPIO pins
 
button = gpiozero.Button(26) # GPIO17 connects to button 
 
while True:
  if button.is_pressed:
    print("tolong!")
  else:
    print("")