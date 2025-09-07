# installation 

create an virtual env:
```
python -m venv ~/cds
source ~/cds/bin/activate
```

install dependencies
```
pip install requests pyinput flask pygame flask pillow
```

# flipping screen horizontally

```
export DISPLAY=:0
wlr-randr --output HDMI-A-1 --transform flipped
```

