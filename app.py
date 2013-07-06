from flask import Flask, url_for, request, Response, session
from flask import render_template
import sys, struct, re, json, sqlite3, os
from datetime import date, datetime
from functools import wraps
from secrets import user, passwd, debug, key

#test


def check_auth(username, password):
    return username == user and password == passwd

def authenticate():
    return Response(
            "Could not verify access level for url.\n"
            "You have to login with proper credentials", 401,
            {'WWW-Authenticate': 'Basic realm="Login Required'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def expand_string(string):
    res = string
    while "\xfc" in res:
        number = res[res.find("\xfc")+1]
        if number == "\x03":
            res = res.replace("\xfc\x03", "\x30\x30\x30")
        elif number == "\x04":
            res = res.replace("\xfc\x04", "\x30\x30\x30\x30")
        elif number == "\x05":
            res = res.replace("\xfc\x05", "\x30\x30\x30\x30\x30")
        elif number == "\x06":
            res = res.replace("\xfc\x06", "\x30\x30\x30\x30\x30\x30")
        else:
            break
    return res


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

def get_payment_details(string, number):
    res = []
    temp = string.split("\xfd\x08\xfc\x08")[0]
    entries = temp.split("\xfd\x08")

    for e in entries:
        etemp = expand_string(e)
        payment_method = etemp[12]
        if payment_method not in ["B","C","K"]:
            payment_method = "U"
        try:
            d = str(struct.unpack(">I", etemp[8:12])[0])
            pay_date = date(int(d[:4]),int(d[4:6]),int(d[6:]))
            res.append((int(etemp[:8]),pay_date, payment_method))
        except ValueError:
            print "oops in append!!"
            print etemp[:8]
    return res


class Student:
    def __init__(self, identifier, name, street, number, zip_code, city, ll_type, tel, id_nr, birth_town, birthday):
        self.identifier = identifier
        self.name = unicode(name, "cp1252")
        self.street = unicode(street, "cp1252")
        self.number = number
        self.zip_code = zip_code
        self.city = city
        self.payments = []
        self.ll_type = ll_type
        self.tel = tel
        self.id_nr = id_nr
        self.birth_town = birth_town
        self.birthday = birthday
        self.unique = "1" + "/" + self.identifier[6:] + "/" + self.identifier[2:6]

    def get_naam(self):
	splitted = self.name.split(" ")
	return " ".join(splitted[:-1])

    def get_voornaam(self):
	splitted = self.name.split(" ")
	return splitted[1]

    def get_id_nr(self):
	return self.id_nr[:3] + "-"+ self.id_nr[3:-2] + "-" + self.id_nr[-2:]

    def append_payments(self, payments):
        self.payments.extend(payments)

    def get_payments_between(self, date1, date2):
        return filter(lambda (x,y,z): date1 <= y <= date2, self.payments)

    def get_total_paid(self):
	total = 0
	for p in self.payments:
	    total += p[0]
	return total

    total_paid = property(get_total_paid)

    def get_header(self):
        res = self.identifier + " " + self.name
        res += "\n" + self.street + " " + self.number + "\n"
        res += self.zip_code + " " + self.city
        return res

    def to_string(self):
        res = self.identifier + " " + self.name
        res += "\n" + self.street + " " + self.number + "\n"
        res += self.zip_code + " " + self.city
        res += "\n" + str(self.payments)
        return res

def read_database_files():
    f = open("BST/llal")
    lines = f.readlines()
    content = "".join(lines)
    students = []

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
        temp = string[index: index + 25].split(chr(253))
        index = index + len(temp[0])
        name = temp[0]
        if string[index] == "\xfd":
            index = index + 2
        regex = re.compile(".*(\d{8})[ABCDE].*")
        m = regex.match(string[index:index+20])
        if string[index:index+5] == "\x32\x30\xfe\x31\x05":
            print identifier
            print "11111111"
            index = index + 6
        elif string[index:index+5] == "\x32\x30\xfe\x31\x04":
            print identifier
            print "11111111"
            index = index + 7
        elif m:
            index = index + m.start() + 8
        else:
            print ":".join("{0:x}".format(ord(c)) for c in string[index: index+20])
            print "error: ", string[index: index + 20]

        ll_type = string[index: index+2]
        index = index + 2
        street = string[index: index+40].split(chr(253))[0]
        if len(street)>20:
            street = street[:20]
        index = index + len(street)
        if string[index] == "\xfd":
            index = index + 2

        m = re.match(r"(.*)(\d\d\d\d[A-Z][A-Z][A-Z\-]+\W)", string[index: index+40])
        if m:
            pattern = re.compile("[\W_]+")
            number = pattern.sub('',m.group(1))
            code = m.group(2)[:4]
            town = m.group(2)[4:-1]
            index = index + len(m.group(1) + m.group(2)) +1
        else:
            m = re.match(r"(.*)(\d..[A-Z][A-Z][A-Z]+\W)", string[index: index+40])
            if m:
                pattern = re.compile("[\W_]+")
                number = pattern.sub('',m.group(1))
                code = m.group(2)[0] + "000"
                town = m.group(2)[3:-1]
                index = index + len(m.group(1) + m.group(2)) +1
            else:
                print "error"
                print string[index: index+20]
                print ":".join("{0:x}".format(ord(c)) for c in string[index: index+20])
                sys.exit()
        m = re.match(r"([A-Z\-]{4}[A-Z\-]*)", string[index: index+40])
        birth_town = ""
        birthday = ""
        if m:
            birth_town = m.group(1)
            try:
                birthday = str(int("".join("{0:x}".format(ord(c)).rjust(2, "0") for c in string[index + len(m.group(1)) + 2: index + len(m.group(1)) + 6]), 16))
                if 1900 < int(birthday[:4]) < 2100:
                    birthday = birthday[6:] + '/' + birthday[4:6] + "/" + birthday[:4]
                else:
                    birthday = ""
            except:
                print "error while looking for birthday"
        m = re.match(r"(.*)(59[01]\d{9})", string[index: index+40])
        id_nr = ""
        if m:
            id_nr = m.group(2)
            index = index + len(id_nr) + len(m.group(1))
        else:
            m = re.match(r"(.*)(B0\d{7})", string[index: index+40])
            if m:
                id_nr = m.group(2)
                index = index + len(id_nr) + len(m.group(1))
            else:
                print "newerror"
                print string[index: index+40]
                print ":".join("{0:x}".format(ord(c)) for c in string[index: index+40])
        tel = ""
        m = re.match(r".*(05\d{7})", string[index: index+70])
        if m:
                tel = m.group(1)
                index = len(tel) + index
        else:
                m = re.match(r".*(04\d{8})", string[index: index+70])
                if m:
                    tel = m.group(1)
                    index = len(tel) + index
                else:
                    print "newtelerror"
                    print string[index: index+40]
                    print ":".join("{0:x}".format(ord(c)) for c in string[index: index+40])
        print tel


        students.append(Student(identifier, name, street, number, code, town, ll_type, tel, id_nr, birth_town, birthday))


    f = open("BST/llbe")

    lines = f.readlines()

    content = "".join(lines)

    indexes = [m.start() for m in re.finditer('012....?..\dE', content)]

    payment_details = {}
    for i in indexes:
            if content[i+5:i+7] == "\xfc\x03":
                identifier = content[i:i+5] + "000" + content[i+7:i+9]
            elif content[i+6:i+8] == "\xfc\x03":
                identifier = content[i:i+6] + "000" + content[i+8:i+9]
            else:
                identifier = content[i:i+10]
                currency = content[i+10]
            try:
                int(identifier)
            except ValueError:
                print "invalid identifier error", identifier
                print ":".join("{0:x}".format(ord(c)) for c in identifier)
                continue
            m = re.match(r".*\W(\d\d)", content[i+11:i+100])
            try:
                if content[i+5:i+7] == "\xfc\x03":
                    if content[i+22:i+24] == "\x31\xfc":
                        nb_payments = 10
                        payments = get_payment_details(content[i+24:], nb_payments)
                    elif content[i+22:i+24] == "\xfc\x0a" or content[i+22:i+24] == "\xfd\x08" or content[i+22:i+24] == "\x08\xfc":
                        nb_payments = 0
                        payments = []
                    else:
                        #print ":".join("{0:x}".format(ord(c)) for c in content[i+22:i+24])
                        nb_payments = int( content[i+22:i+24])
                        payments = get_payment_details(content[i+24:], nb_payments)
                elif content[i+6:i+8] == "\xfc\x03":
                    if content[i+22:i+24] == "\x31\xfc":
                        nb_payments = 10
                        payments = get_payment_details(content[i+24:], nb_payments)
                    elif content[i+22:i+24] == "\xfc\x0a" or content[i+22:i+24] == "\xfd\x08" or content[i+22:i+24] == "\x08\xfc":
                        nb_payments = 0
                        payments = []
                    else:
                        #print ":".join("{0:x}".format(ord(c)) for c in content[i+22:i+24])
                        nb_payments = int( content[i+22:i+24])
                        payments = get_payment_details(content[i+24:], nb_payments)
                else:
                    if content[i+23:i+25] == "\x31\xfc":
                        nb_payments = 10
                        payments = get_payment_details(content[i+24:], nb_payments)
                    elif content[i+23:i+25] == "\xfc\x0a" or content[i+23:i+25] == "\xfd\x08" or content[i+23:i+25] == "\x08\xfc":
                        nb_payments = 0
                        payments = []
                    else:
                        #print ":".join("{0:x}".format(ord(c)) for c in content[i+23:i+25])
                        nb_payments = int( content[i+23:i+25])
                        payments = get_payment_details(content[i+25:], nb_payments)
                if not payment_details.has_key(identifier):
                    payment_details[identifier] = []
                payment_details[identifier].extend(payments)
            except ValueError:
                if int(identifier[2:6]) > 2011:
                    print "nb of payments error", identifier
                    print ":".join("{0:x}".format(ord(c)) for c in content[i: i+10])
                    print ":".join("{0:x}".format(ord(c)) for c in content[i+22:i+26])
                    print ":".join("{0:x}".format(ord(c)) for c in content[i+12:i+65])
                    print content[i+12:i+65]
                pass
    for entry in students:
        #print "-----------------------------"
        try:
            entry.append_payments(payment_details[entry.identifier])
        except KeyError:
            #print "no payments for: " + entry.identifier
            pass
        #print entry.to_string()
    students.reverse()
    return students

def get_students_with_payments_between(students, date1, date2):
    return filter(lambda s: s.get_payments_between(date1, date2), students)

def adapt_string_for_getuigeschrift(string):
    l = []
    for i in range(0,32):
	if i < len(string):
            l.append(string[i].upper())
	else:
	    l.append(" ")
    return l

def prefill_date():
    t = datetime.today()
    return str(t.day) + "/" + str(t.month) + "/" + str(t.year)

students = read_database_files()

feb = get_students_with_payments_between(students, date(2013,2,1), date(2013,2,28))
mar = get_students_with_payments_between(students, date(2013,3,1), date(2013,3,31))
apr = get_students_with_payments_between(students, date(2013,4,1), date(2013,4,30))
may = get_students_with_payments_between(students, date(2013,5,1), date(2013,5,31))
jun = get_students_with_payments_between(students, date(2013,6,1), date(2013,6,30))
jul = get_students_with_payments_between(students, date(2013,7,1), date(2013,7,31))
#remember: function must not have the same name....!!!



app = Flask(__name__)

@app.route('/')
@requires_auth
def home():
    return render_template('index.html')

@app.route('/contract', methods=["GET", "POST"])
def contract():
    if request.method == "GET":
	d = {"Naam": "", "Woonplaats":"", "Adres":"", "Telefoon":"", "Geborente":"", "Op":"", "Opmerkingen":"", "Datum":prefill_date()}
	t = {"Inschrijving":"", "Theoriecursus":"","Praktijkles":"", "Examenbegeleiding":"", "Voorschot":"0"}
        identifier = request.args.get("student", "")
        try:
            int(identifier)
        except:
            identifier = ""
        if (identifier != "") and (len(students) > int(identifier)):
            student = students[int(identifier) - 1]
            d["Naam"] = student.name
            d["Woonplaats"] = student.city
            d["Adres"] = student.street + " " + student.number
            d["Telefoon"] = student.tel
            d["Geborente"] = student.birth_town
            d["Op"] = student.birthday
        return render_template('contract_form.html', fields=d, tarieven=t)
    else:
	d = {}
	d["Naam"] = request.form["Naam"]
        d["Woonplaats"] =request.form["Woonplaats"]
        d["Adres"] =request.form["Adres"]
        d["Telefoon"] =request.form["Telefoon"]
        d["Geborente"] =request.form["Geborente"]
        d["Op"] =request.form["Op"]
	d["Inschrijving"] = request.form["Inschrijving"]
	d["Theoriecursus"] = request.form["Theoriecursus"]
	d["Praktijkles"] = request.form["Praktijkles"]
	d["Examenbegeleiding"] = request.form["Examenbegeleiding"]
	d["Voorschot"] = request.form["Voorschot"]
	d["Opmerkingen"] = request.form["Opmerkingen"]
	d["Both"] = len(request.form.getlist("type")) == 2
	d["Theorie"] = "Theorie" in request.form.getlist("type")
	d["Praktijk"] = "Praktijk" in request.form.getlist("type")
	d["Categorie"] = request.form["categorie"]
	d["Datum"] = request.form["Datum"]
        return render_template('contract.html', values=d)





@app.route('/getuigeschrift', methods=["GET", "POST"])
@requires_auth
def hello():
    identifier = request.args.get("student", "")
    print identifier
    try:
	    int(identifier)
    except:
	    identifier = ""

    if request.method=="GET":
	if identifier != "" and len(students) > int(identifier):
	    student = students[int(identifier) - 1]
	    n = student.get_naam()
	    vn = student.get_voornaam()
	    gd = student.birthday
	    gp = student.birth_town
	    nrid = student.get_id_nr()
	    a = student.street + " " + student.number
	    pc = student.zip_code
	    g = student.city
	    nrin = student.unique
	    nrrr = ""
	    l = ""
	else:
	    n = ("")
            vn = ("")
            gd = ("")
            gp = ""
            nrid = ("")
            a = ""
            pc = ("")
            g = ""
            nrin = ("")
            nrrr = ("")
            l = ""
        d = "Leen Vanslambrouck"
        e = "2577"
        elng = ""
	dat = prefill_date()
        arijschool = "Rijschool Erasmus Sint-Jorisstraat 12 8500 Kortrijk"
        return render_template('getuigeschrift_form.html', naam = n, voornaam = vn, geboortedatum = gd, geboorteplaats = gp, identiteitskaart = nrid, adres = a, postcode = pc, gemeente= g, inschrijving = nrin, rijksregister=nrrr, directeur = d, erkenningsnummer = e, lesuren = l, eerstelesnoggeldig=elng, adresrijschool=arijschool, datum=dat)
    else:
	n = adapt_string_for_getuigeschrift(request.form["naam"])
        vn = adapt_string_for_getuigeschrift(request.form["voornaam"])
        gd = adapt_string_for_getuigeschrift(request.form["geboortedatum"] + " " + request.form["geboorteplaats"])
        nrid = adapt_string_for_getuigeschrift(request.form["nrid"])
        a = adapt_string_for_getuigeschrift(request.form["adres"])
        pc = adapt_string_for_getuigeschrift(request.form["postcode"] + " " + request.form["gemeente"])
        nrin = adapt_string_for_getuigeschrift(request.form["nrin"])
        nrrr = adapt_string_for_getuigeschrift(request.form["nrrr"])
        d = request.form["directeur"]
        e = request.form["erkenningsnummer"]
        l = request.form["lesuren"]
        elng = request.form["eerstelesnoggeldig"]
        arijschool = request.form["adresrijschool"]
        rb = False
        rbe = False
        rc = False
        rce = False
        rb96= False
	dat = request.form["datum"]
        if request.form["type"] == "bekwaamheidsattest":
            ba = True
            gs = False
        else:
            ba = False
            gs = True
            if request.form["getuigeschrift"] == "B":
	        rb = True
            elif request.form["getuigeschrift"] == "BE":
		rbe = True
            elif request.form["getuigeschrift"] == "C":
		rc = True
            elif request.form["getuigeschrift"] == "CE":
		rce = True
            elif request.form["getuigeschrift"] == "B96":
		rb96 = True

        return render_template('getuigeschrift.html', naam = n, voornaam = vn, geboortedatum = gd, identiteitskaart = nrid, adres = a, postcode = pc, inschrijving = nrin, rijksregister=nrrr, directeur = d, erkenningsnummer = e, lesuren = l, eerstelesnoggeldig=elng, adresrijschool=arijschool, attest=ba, getuigeschrift=gs, rrb=rb, rrbe=rbe, rrc=rc, rrce=rce, rrb96=rb96, datum=dat)

@app.route('/save-invoice', methods=["POST"])
@requires_auth
def save_invoice():
    data = json.loads(request.form["data"])
    print "before"
    #session["date"] = data["date"]
    print "before"
    #session["number"] = str(int(data["nummer"])+1)
    print "before"
    #print session["date"]
    print "before"
    #print session["number"]
    conn = sqlite3.connect("database")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO invoices(title, reference, date, nummer, total) VALUES(?,?,?,?,?)",(data["title"], data["referentie"], data["date"], data["nummer"], data["due"]))
    conn.commit()
    invoice_id = cursor.lastrowid
    for entry in data["entries"]:
        print entry["code"]
        cursor.execute("INSERT INTO invoice_entries(factuur_id, code, omschrijving, cost, btw, qty) VALUES(?,?,?,?,?,?)",(invoice_id, entry["code"], entry["omschrijving"], entry["cost"], entry["btw"], entry["qty"]))
    conn.commit()
    conn.close()
    return request.form["data"]

@app.route('/edit-invoice', methods=["POST"])
@requires_auth
def edit_invoice():
    data = json.loads(request.form["data"])
    conn = sqlite3.connect("database")
    cursor = conn.cursor()
    cursor.execute("UPDATE invoices SET total=? where Id=?",(data["due"], data["id"]))
    conn.commit()
    cursor.execute("DELETE FROM invoice_entries WHERE factuur_id=?", (data["id"],))
    conn.commit()
    for entry in data["entries"]:
        cursor.execute("INSERT INTO invoice_entries(factuur_id, code, omschrijving, cost, btw, qty) VALUES(?,?,?,?,?,?)",(data["id"], entry["code"], entry["omschrijving"], entry["cost"], entry["btw"], entry["qty"]))
    conn.commit()
    conn.close()
    return request.form["data"]

@app.route('/list_students')
@requires_auth
def list_students():
    s = []

    for entry in students:
        #payments = entry.get_payments_between(begin, end)
        s.append(entry)

    return render_template('student_list.html', students = s, link="invoice")

@app.route('/list_feb')
@requires_auth
def list_feb():
    s = []

    for entry in feb:
        #payments = entry.get_payments_between(begin, end)
        s.append(entry)

    return render_template('febstudent_list.html', students = s, link="feb")

@app.route('/list_mar')
@requires_auth
def list_mar():
    s = []

    for entry in mar:
        #payments = entry.get_payments_between(begin, end)
        s.append(entry)

    return render_template('febstudent_list.html', students = s, link="mar")

@app.route('/list_apr')
@requires_auth
def list_apr():
    s = []

    for entry in apr:
        #payments = entry.get_payments_between(begin, end)
        s.append(entry)

    return render_template('febstudent_list.html', students = s, link="apr")
@app.route('/list_may')
@requires_auth
def list_may():
    s = []

    for entry in may:
        #payments = entry.get_payments_between(begin, end)
        s.append(entry)

    return render_template('febstudent_list.html', students = s, link="may")
@app.route('/list_jun')
@requires_auth
def list_jun():
    s = []

    for entry in jun:
        #payments = entry.get_payments_between(begin, end)
        s.append(entry)

    return render_template('febstudent_list.html', students = s, link="jun")
@app.route('/list_jul')
@requires_auth
def list_jul():
    s = []

    for entry in jul:
        #payments = entry.get_payments_between(begin, end)
        s.append(entry)

    return render_template('febstudent_list.html', students = s, link="jul")

@app.route('/student/<int:identifier>')
@requires_auth
def student(identifier):
    identifier = identifier - 1
    if identifier < len(students):
        if (identifier -1) < 0:
            ppu = url_for('list_students')
        else:
            ppu = url_for('student',identifier = identifier)
        if (identifier + 1) > len(students):
            npu = url_for('list_students')
        else:
            bla = identifier + 2
            npu = url_for('student', identifier = bla)
        return render_template('student.html', identifier = identifier+1,student = students[identifier], next_profile_url = npu, previous_profile_url = ppu)
    else:
        return list_students()
@app.route('/reload_data')
@requires_auth
def reload_data():
    global students
    students = read_database_files()
    return "done"

@app.route('/invoice/<int:identifier>')
@requires_auth
def invoice(identifier):
    s = students[identifier-1]
    return make_invoice(s)

@app.route('/feb/<int:identifier>')
@requires_auth
def february(identifier):
    s = feb[identifier-1]
    return make_invoice(s)

def make_invoice(s):
    conn = sqlite3.connect("database")
    cursor = conn.cursor()
    rows = []
    total = 0
    for row in cursor.execute("SELECT * FROM invoices where reference=?", (s.unique, )):
        rows.append(row)
	try:
	    if not total=="error":
		print row[5][1:].replace(",",".")
	        total += float(row[5][1:].replace(",","."))
	except:
	    total = "error"
    conn.close()
    if len(rows)<1:
        rows = None
    if not "date" in session:
        temp = date.today()
        datum = str(temp.day) + "/" + str(temp.month) + "/" + str(temp.year)
    else:
        datum = session["date"]
    if not "number" in session:
        number = "123"
    else:
        number = session["number"]
    return render_template('aprinvoice.html', student = s, invoices = rows, date = datum, number = number, totaal=str(total).replace(".",","))
@app.route('/mar/<int:identifier>')
@requires_auth
def march(identifier):
    s = mar[identifier-1]
    return make_invoice(s)
@app.route('/apr/<int:identifier>')
@requires_auth
def april(identifier):
    s = apr[identifier-1]
    return make_invoice(s)
@app.route('/may/<int:identifier>')
@requires_auth
def mei(identifier):
    s = may[identifier-1]
    return make_invoice(s)
@app.route('/jun/<int:identifier>')
@requires_auth
def june(identifier):
    s = jun[identifier-1]
    return make_invoice(s)
@app.route('/jul/<int:identifier>')
@requires_auth
def july(identifier):
    s = jul[identifier-1]
    return make_invoice(s)
    
@app.route('/saved-invoice/<int:identifier>')
@requires_auth
def saved_invoice(identifier):
    conn = sqlite3.connect("database")
    cursor = conn.cursor()
    rows = []
    for row in cursor.execute("select * from invoices where Id=?", (identifier, )):
        rows.append(row)
    if len(rows)==0:
        conn.close()
        return "Factuur niet gevonden"
    entries = []
    print "before entries"
    for entry in cursor.execute("select * from invoice_entries where factuur_id=?", (identifier, )):
        entries.append(entry)

    if len(entries) == 0:
        conn.close()
        return "Geen data in factuur"
    print "after entries"
    (identifier, title, reference, date, nummer, total) = rows[0]
    conn.close()
    print "before render"
    return render_template('saved_invoice.html', title=title, fnr = nummer, date=date, ref=reference, entries=entries)
    
@app.route('/test')
@requires_auth
def test():
    return os.getcwd() + str(os.path.isfile("database"))

if __name__ == '__main__':
    app.secret_key = key
    if debug:
        app.debug = True
        app.run()
    else:
        app.run(host="0.0.0.0", port=4343)
