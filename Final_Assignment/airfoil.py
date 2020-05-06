
# this file contains functions used for reading airfoil coordinates from a text file

white_list = [" ", "\n", "\t"]      # any of these are ignored before or after coordinates
separator = [" ", ",", "\t"]        # any of these are taken as number separators

# determine if line is empty
def is_empty(line):
    empty = True
    if len(line) > 0:
        for c in line:
            if c not in white_list:
                empty = False
    return empty

# convert the string of one line into coordinates
def read_coords(line):
    x, y = "", ""
    sub_stage = 0       # this means before fist coordinate
    for c in line:
        if c in separator:  # check for separator symbol
            if x != "":     # if x is not empty
                sub_stage = 1   # change to reading y
            if y != "":     # if y is not empty, end
                break
        else:
            if sub_stage == 0:      # add to x if in mode 0
                x = x + c
            elif sub_stage == 1:    # add to y if reading y
                y = y + c
    return float(x), float(y)


def get_airfoil(name):
    f = open("airfoils/" + name + ".txt")
    mode = "unknown"        # two types of files are accepted, mode stores this information

    found_first = False
    line = f.readline()
    while not found_first:  # read lines until first coordinate is found
        if is_empty(line):
            line = f.readline()
        else:
            x, y = read_coords(line)    # if first x is small then mode is normal, otherwise reversed
            if x < 0.1:
                mode = "normal"
            if x > 0.9:
                mode = "reversed"
            break

    if mode == "normal":
        stage = 1
        xt, yt = [], []
        xb, yb = [], []
        while True:
            if is_empty(line):
                if stage == 3:
                    break
            else:
                x, y = read_coords(line)

                if stage == 1:
                    xt.append(x)
                    yt.append(y)
                    if x == 1:
                        stage = 2
                else:
                    xb.append(x)
                    yb.append(y)
                    stage = 3
            line = f.readline()

        if yb[-1] != yt[-1]:
            yb[-1] = yt[-1]
        f.close()
        return list(reversed(xb))+xt, list(reversed(yb))+yt

    elif mode == "reversed":
        x_list, y_list = [], []
        stage = 1
        while True:
            if is_empty(line):
                if stage == 3:
                    break
            else:
                x, y = read_coords(line)
                x_list.append(x)
                y_list.append(y)
                if x < 0.1:
                    stage = 2
                elif stage == 2 and x > 0.9:
                    stage = 3
            line = f.readline()
        if y_list[0] != y_list[-1]:
            y_list[-1] = y_list[0] = y_list[0]/2 + y_list[-1]/2
        f.close()
        return list(reversed(x_list)), list(reversed(y_list))


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    x, y = get_airfoil("whitcomb.txt")
    plt.plot(x, y)

    plt.axis("equal")
    plt.show()
