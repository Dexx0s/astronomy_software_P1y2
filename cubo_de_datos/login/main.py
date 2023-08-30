import os
import tkinter
from tkinter import *
from tkinter import messagebox

##fijar el entorno de la carpeta para la ejecucion// no sacar
current_directory = os.getcwd()
file_directory = os.path.dirname(os.path.abspath(__file__))
os.chdir(file_directory)
new_current_directory = os.getcwd()

##creacion de la ventana en tk
Login=Tk()
Login.geometry("400x600")
Login.title("Bienvenido")
Login.iconbitmap("icon.ico")##icono de la ventana

##subiendo imagen de login al tk
image=PhotoImage(file="login_icon.png")
image=image.subsample(2,2)
label=Label(image=image)
label.pack()

##texto de la ventana

Label(text="Acceso de usuarios",bg="oldlace",fg="black",width="400",height="3",font=("Calibrí",15)).pack()
Label(text="").pack()
Label(text="").pack()
Button(text="registrar usuario",fg="black",height="3",width="200").pack()
Label(text="").pack()
Button(text="Logear usuario",bg="oldlace",fg="black",height="3",width="200").pack()


Login.mainloop()