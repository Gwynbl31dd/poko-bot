# Poko Bot

Update of the freenove hexapod robot with a Raspberry Pi.

This project is tentative and is not yet complete. I aim to expend the capabilities of the freenove hexapod robot to make it more autonomous and to add more features.


## Autostart

```
cp /home/apaulin/poko-bot/start.sh /home/apaulin/
sudo chmod 777 start.sh
mkdir ~/.config/autostart/
```

```
sudo nano .config/autostart/start.desktop
```

And edit

```
[Desktop Entry]
Type=Application
Name=start
NoDisplay=true
Exec=/home/apaulin/start.sh
```

```
sudo chmod +x .config/autostart/start.desktop
```

and finally

```
sudo reboot
```

