import re

def readMap():
    map={}
    string = ''
    pattern = re.compile('\d+,\d+ ')
    with open('./map.txt', mode='r', encoding='utf-8') as f:
        for line in f:
            string = string + line
    
    # print(string)

    entrys = pattern.findall(string)
    map.clear()
    for entry in entrys:
        # print(entry)
        array = re.split('[, ]', entry)
        key = int(array[0])
        value = int(array[1])
        map[key] = value
    return map

def writeMap(map):
   
    string = ''
    for key, value in map.items():
        string += str(key) + ',' + str(value) + ' '
    with open('./map.txt', mode='w', encoding='utf-8') as f:
        f.write(string)


if __name__ == "__main__":
    map = {1:2, 3:3, 33:7}
    writeMap(map)
    print(readMap())
    