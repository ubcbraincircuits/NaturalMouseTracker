import os

i = 0
x = 0
for filename in os.listdir('./darknet/micePics/'):
    dst = "individual_mouse" + str(i) + '.png'
    if "png" in filename and x % 25 == 0:
        src =  "./darknet/micePics/" + filename
        dst = './darknet/micePics/' + dst
        os.rename(src, dst)
        i += 1
    x += 1
