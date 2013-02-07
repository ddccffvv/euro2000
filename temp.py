import sys

def get_identifier(string):
    if string[12]!="0":
        print "ERROR: ", string
        print string[12]
        return (None, None)
    else:
        if string[17:20] == "\x33\xfc\x03":
            return (string[12:18] + "000" + string[20], 21)
        elif string[17:20] == "\x31\xfc\x03":
            return (string[12:18] + "000" + string[20], 21)
        elif string[17:20] == "\x32\xfc\x03":
            return (string[12:18] + "000" + string[20], 21)
        elif string[17:20] == "\x38\xfc\x03":
            return (string[12:18] + "000" + string[20], 21)
        elif string[17:20] == "\x39\xfc\x03":
            return (string[12:18] + "000" + string[20], 21)
        elif string[17:20] == "\x37\xfc\x03":
            return (string[12:18] + "000" + string[20], 21)
        elif string[16:19] == "\x31\xfc\x03":
            return (string[12:17] + "000" + string[19:21], 21)
        elif string[16:19] == "\x31\xfc\x04":
            return (string[12:17] + "0000" + string[19], 20)
        elif re.match(r"^\d+$", string[17:22]):
            return (string[12:22], 22)
        else:
            print "ERROR: " + string
            print ord(string[18]), ord(string[19]), ord(string[20])
            print  ":".join("{0:x}".format(ord(c)) for c in string[16:20])
            return (None,None)

f = open("BST/llal")

lines = f.readlines()

content = "".join(lines)

import re

#indexes = [m.start() for m in re.finditer('B [A-Z]', content)]
indexes = [m.end() for m in re.finditer('[\x00]{65}\x01', content)]

previous = 0
length = 450
for entry in indexes:
    previous += 1
    string = content[entry:entry+length]
    #regex = re.compile(r"([A-Z]{4})")
    #m = regex.match(string)
    (identifier, index) = get_identifier(string)
    if not identifier:
        continue
    print "----------------------------"
    print identifier
    temp = string[index: index + 25].split(chr(253))
    index = index + len(temp[0])
    print temp[0], len(temp)
    if string[index] == "\xfd":
        index = index + 2
    regex = re.compile(".*(\d{8})[ABCDE].*")
    m = regex.match(string[index:index+20])
    if string[index:index+5] == "\x32\x30\xfe\x31\x05":
        print "11111111"
        index = index + 6
    elif string[index:index+5] == "\x32\x30\xfe\x31\x04":
        print "11111111"
        index = index + 7
    elif m:
        print m.group(1)
        index = index + m.start() + 8
    else:
        print ":".join("{0:x}".format(ord(c)) for c in string[index: index+20])
        print "error: ", string[index: index + 20]

    print string[index: index+2]
    index = index + 2
    street = string[index: index+40].split(chr(253))[0]
    if len(street)>20:
        street = street[:20]
    print street
    index = index + len(street)
    print ":".join("{0:x}".format(ord(c)) for c in string[index: index+20])
    if string[index] == "\xfd":
        index = index + 2
    number = string[index: index+10].split(chr(253))[0]
    print number
    index = index + len(number) + 2 #two extra for fd
    print string[index:index+4]
    print ":".join("{0:x}".format(ord(c)) for c in string[index: index+20])



sys.exit()


values = []

for entry in range(0, 180):
    values.append([])

print indexes

for entry in indexes:
    splitted = content[entry+60:entry+90]
    print "\""+splitted+"\""
    string =  ":".join("{0:x}".format(ord(c)).ljust(2,"0") for c in splitted)
    print string
    for count, entry in enumerate(string.split(":")):
        values[count].append(entry)

for i, entry in enumerate(values):
    print i, "values:", set(entry)


#p = content.split(chr(0x00)*16+chr(0x01))
#p = filter(lambda x: len(x)>0, p)
#for entry in p:
    #print "----------------------------"
    #value = entry.split(chr(253))[0]
    #print "01:" + "{0:x}".format(ord(value[0]))
    #print ":".join("{0:x}".format(ord(c)) for c in value[12:22])
    #print value[12:22]

    #print ":".join("{0:x}".format(ord(c)) for c in value[22:])
    #print "\""+ value[22:47]+ "\"", len(value[22:47])

    #for b in entry.split(chr(253)):
        #print "\t" + b + " " + str(len(b))

#print len(p)
