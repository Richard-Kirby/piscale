from guizero import App, TextBox, PushButton, Text

def update_text():
    label.value = name.value

app = App()
label = Text(app, text="What's your name?")
name = TextBox(app)
button = PushButton(app, command=update_text)

app.display()
