import os
from datetime import datetime

from bson import ObjectId
from flask import Flask, request, render_template, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import pymongo

App_Root = os.path.dirname(__file__)
App_Root = App_Root + "/static"


app = Flask(__name__)
# In production this should come from an environment variable, not be hard-coded.
app.secret_key = os.environ.get("SECRET_KEY", "zoo_Ticket_Management")

# Connection string can be overridden via the MONGO_URI environment variable.
mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
my_conn = pymongo.MongoClient(mongo_uri)
mydb = my_conn["zoo_Ticket_Management"]
admin_col = mydb["admin"]
customer_col = mydb["customer"]
payment_col = mydb["payment"]
booking_col = mydb["booking"]
ticket_col = mydb["ticket"]
stall_col = mydb["stall"]
activities_col = mydb["activities"]
refunds_col = mydb['refunds']


# Seed a default admin account on first run. The password is stored hashed,
# never in plain text.
if admin_col.count_documents({}) == 0:
    admin_col.insert_one({
        "username": "admin",
        "password": generate_password_hash("admin"),
    })


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/admin_login")
def admin_login():
    message = request.args.get("message")
    return render_template("admin_login.html", message=message)


@app.route("/admin_login1", methods=["post"])
def admin_login1():
    username = request.form.get("username")
    password = request.form.get("password")
    admin = admin_col.find_one({"username": username})
    if admin and check_password_hash(admin["password"], password):
        session["admin_id"] = str(admin["_id"])
        session["role"] = 'Admin'
        return redirect("/admin_home")
    else:
        return redirect("/admin_login?message=Invalid Login Details")


@app.route("/admin_home")
def admin_home():
    admin_id = session["admin_id"]
    query = {"_id": ObjectId(admin_id)}
    admin = admin_col.find_one(query)
    return render_template("admin_home.html", admin=admin)


@app.route("/customer_register")
def customer_register():
    return render_template("customer_register.html")


@app.route("/customer_register1", methods=["post"])
def customer_register1():
    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    dob = request.form.get("dob")
    password = request.form.get("password")
    gender = request.form.get("gender")
    query = {"$or": [{"email": email}, {"phone": phone}]}
    count = customer_col.count_documents(query)
    if count == 0:
        query = {"name": name, "email": email, "phone": phone, "dob": dob,
                 "password": generate_password_hash(password), "gender": gender}
        customer_col.insert_one(query)
        return render_template("message.html", message="Customer Registered Successful")
    else:
        return render_template("message.html", message="Duplicate Entry")


@app.route("/customer_login")
def customer_login():
    return render_template("customer_login.html")


@app.route("/customer_login1", methods=['post'])
def customer_login1():
    email = request.form.get("email")
    password = request.form.get("password")
    customer = customer_col.find_one({"email": email})
    if customer and check_password_hash(customer["password"], password):
        session["customer_id"] = str(customer["_id"])
        session["role"] = 'Customer'
        return redirect("/customer_home")
    else:
        return render_template("message.html", message="Invalid Login Details")


@app.route("/view_customers")
def view_customer():
    customers = list(customer_col.find())
    if len(customers) == 0:
        return render_template("message.html", message="No Details Found")
    return render_template("view_customers.html", customers=customers)


@app.route("/customer_home")
def customer_home():
    customer_id = session["customer_id"]
    query = {"_id": ObjectId(customer_id)}
    customer = customer_col.find_one(query)
    return render_template("customer_home.html", customer = customer)


@app.route("/add_activity")
def add_activity():
    return render_template("add_activity.html")


@app.route("/add_activity1", methods=['post'])
def add_activity1():
    activity_name = request.form.get("activity_name")
    query = {"activity_name": activity_name}
    count = activities_col.count_documents(query)
    if count == 0:
        query = {"activity_name": activity_name}
        activities_col.insert_one(query)
        return {"message": "Activity Added Successfully"}
    else:
        return {"message": "Duplicate Details"}


@app.route("/get_activities")
def get_activities():
    activities = activities_col.find()
    return render_template("view_activities.html", activities=activities)


@app.route("/add_stalls")
def add_stalls():
    message = request.args.get("message")
    activities = activities_col.find()
    stalls = stall_col.find()
    if stalls == None:
        return {}
    return render_template("add_stalls.html", activities=activities, message=message, stalls=stalls, get_activity_ids=get_activity_ids)


@app.route("/add_stall1", methods=['post'])
def add_stall1():
    stall_name = request.form.get("stall_name")
    date = request.form.get("date")
    picture = request.files.get("picture")
    path = App_Root + "/pictures/" + picture.filename
    picture.save(path)
    activity_ids = request.form.getlist("activity_ids")
    activitives_ids = []
    for activity_id in activity_ids:
        activitives_ids.append(ObjectId(activity_id))
    description = request.form.get("description")
    query = {"stall_name": stall_name}
    count = stall_col.count_documents(query)
    if count == 0:
        query = {"stall_name": stall_name, "picture": picture.filename, "date": date, "activity_ids": activitives_ids ,"description": description}
        stall_col.insert_one(query)
        return redirect("/add_stalls?message=Stall Added Successfully")
    else:
        return redirect("/add_stalls?message=Duplicate Stall Name")


def get_activity_ids(activity_id):
    query = {"_id": ObjectId(activity_id)}
    activity = activities_col.find_one(query)
    return activity


@app.route("/add_tickets")
def add_tickets():
    message = request.args.get("message")
    stalls = stall_col.find()
    tickets = ticket_col.find()
    return render_template("add_tickets.html", stalls=stalls, message=message, tickets=tickets, get_stall_id=get_stall_id, available_tickets=available_tickets)


@app.route("/add_ticket1", methods=['post'])
def add_ticket1():
    ticket_title = request.form.get("ticket_title")
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    dob = request.form.get("dob")
    stall_id = request.form.get("stall_id")
    number_of_tickets = request.form.get("number_of_tickets")
    price_for_adults = request.form.get("price_for_adults")
    price_for_children = request.form.get("price_for_children")
    price_for_senior_citizen = request.form.get("price_for_senior_citizen")
    price_for_handy_capped = request.form.get("price_for_handy_capped")
    remaining_tickets = number_of_tickets

    if ticket_title == "Entry Ticket":
        query = {"ticket_title": ticket_title, "number_of_tickets": number_of_tickets, "first_name": first_name, "last_name": last_name, "dob": dob, "remaining_tickets": remaining_tickets, "price_for_adults": price_for_adults, "price_for_children": price_for_children, "price_for_senior_citizen": price_for_senior_citizen, "price_for_handy_capped": price_for_handy_capped}
    else:
        query = {"ticket_title": ticket_title, "stall_id": ObjectId(stall_id),"remaining_tickets": remaining_tickets, "number_of_tickets": number_of_tickets, "first_name": first_name, "last_name": last_name, "dob": dob,  "price_for_adults": price_for_adults, "price_for_children": price_for_children, "price_for_senior_citizen": price_for_senior_citizen, "price_for_handy_capped": price_for_handy_capped}
    ticket_col.insert_one(query)
    return redirect("/add_tickets?message=Tickets Added Successfully")


def get_stall_id(stall_id):
    query = {"_id": ObjectId(stall_id)}
    stall = stall_col.find_one(query)
    return stall


@app.route("/view_tickets")
def view_tickets():
    tickets = ticket_col.find()
    return render_template("view_tickets.html", tickets=tickets, get_stall_id=get_stall_id, available_tickets=available_tickets)


@app.route("/book_entry_ticket")
def book_entry_ticket():
    message = request.args.get("message")
    ticket_id = request.args.get("ticket_id")
    query = {"_id": ObjectId(ticket_id)}
    ticket = ticket_col.find_one(query)
    remaining_tickets = ticket['remaining_tickets']
    return render_template("book_entry_ticket.html", ticket_id=ticket_id, remaining_tickets=remaining_tickets, message=message)


@app.route("/book_entry_ticket1", methods=['post'])
def book_entry_ticket1():
    customer_id = session['customer_id']
    ticket_id = request.form.get("ticket_id")
    query = {"_id": ObjectId(ticket_id)}
    ticket = ticket_col.find_one(query)
    price_for_adults = ticket['price_for_adults']
    price_for_children = ticket['price_for_children']
    price_for_senior_citizen = ticket['price_for_senior_citizen']
    price_for_handy_capped = ticket['price_for_handy_capped']
    remaining_tickets = request.form.get("remaining_tickets")
    booking_date = request.form.get("booking_date")
    booking_date = booking_date.replace("T", " ")
    booking_date = datetime.strptime(booking_date, '%Y-%m-%d %H:%M')
    date = datetime.now()
    booking_status = "Customer Booked Ticket"
    no_of_adult_tickets = request.form.get("no_of_adult_tickets")
    no_of_children_tickets = request.form.get("no_of_children_tickets")
    no_of_senior_citizen_tickets = request.form.get("no_of_senior_citizen_tickets")
    no_of_handy_capped_tickets = request.form.get("no_of_handy_capped_tickets")
    adult_amount = int(no_of_adult_tickets) * int(price_for_adults)
    children_amount = int(no_of_children_tickets) * int(price_for_children)
    senior_citizen_amount = int(no_of_senior_citizen_tickets) * int(price_for_senior_citizen)
    handy_capped_amount = int(no_of_handy_capped_tickets) * int(price_for_handy_capped)
    number_of_tickets = (int(no_of_adult_tickets) + int(no_of_children_tickets) + int(no_of_senior_citizen_tickets) + int(no_of_handy_capped_tickets))
    total_amount = int(adult_amount + children_amount + senior_citizen_amount + handy_capped_amount)
    adults = []
    for i in range(1, int(no_of_adult_tickets) + 1):
        namea = request.form.get("namea" + str(i))
        agea = request.form.get("agea" + str(i))
        adults.append({"name": namea, "age": agea})
    children = []
    for i in range(1, int(no_of_children_tickets) + 1):
        namec = request.form.get("namec" + str(i))
        agec = request.form.get("agec" + str(i))
        children.append({"name": namec, "age": agec})
    senior_citizen = []
    for i in range(1, int(no_of_senior_citizen_tickets) + 1):
        names = request.form.get("names" + str(i))
        ages = request.form.get("ages" + str(i))
        senior_citizen.append({"name": names, "age": ages})
    handy_capped = []
    for i in range(1, int(no_of_handy_capped_tickets) + 1):
        nameh = request.form.get("nameh" + str(i))
        ageh = request.form.get("ageh" + str(i))
        handy_capped.append({"name": nameh, "age": ageh})

    query = {"ticket_id": ObjectId(ticket_id), "customer_id": ObjectId(customer_id), "booking_status": booking_status, "booking_date": booking_date, "date": date, "no_of_adult_tickets": no_of_adult_tickets, "adults": adults, "no_of_children_tickets": no_of_children_tickets, "children": children, "no_of_senior_citizen_tickets": no_of_senior_citizen_tickets, "senior_citizen": senior_citizen, "no_of_handy_capped_tickets": no_of_handy_capped_tickets, "handy_capped": handy_capped, "total_amount": total_amount, "number_of_tickets": number_of_tickets}
    result = booking_col.insert_one(query)
    booking_id = result.inserted_id
    query = {"_id": booking_id}
    booking = booking_col.find_one(query)
    number_of_tickets = booking['number_of_tickets']

    remaining_tickets = int(remaining_tickets) - int(number_of_tickets)
    query = {"_id": ObjectId(ticket_id)}
    query1 = {"$set": {"remaining_tickets": remaining_tickets}}
    ticket_col.update_one(query, query1)
    return render_template("pay_amount.html", booking=booking, get_ticket_id=get_ticket_id, get_stall_id=get_stall_id, get_customer_id=get_customer_id, str=str)


@app.route("/book_stall_ticket")
def book_stall_ticket():
    message = request.args.get("message")
    ticket_id = request.args.get("ticket_id")
    stall_id = request.args.get("stall_id")
    query = {"_id": ObjectId(ticket_id)}
    ticket = ticket_col.find_one(query)
    remaining_tickets = ticket['remaining_tickets']
    return render_template("book_stall_ticket.html", ticket_id=ticket_id, remaining_tickets=remaining_tickets, message=message, stall_id=stall_id)


@app.route("/book_stall_ticket1", methods=['post'])
def book_stall_ticket1():
    customer_id = session['customer_id']
    ticket_id = request.form.get("ticket_id")
    stall_id = request.form.get("stall_id")
    query = {"_id": ObjectId(ticket_id)}
    ticket = ticket_col.find_one(query)
    price_for_adults = ticket['price_for_adults']
    price_for_children = ticket['price_for_children']
    price_for_senior_citizen = ticket['price_for_senior_citizen']
    price_for_handy_capped = ticket['price_for_handy_capped']
    remaining_tickets = request.form.get("remaining_tickets")

    booking_date = request.form.get("booking_date")
    booking_date = booking_date.replace("T", " ")
    booking_date = datetime.strptime(booking_date, '%Y-%m-%d %H:%M')
    date = datetime.now()
    booking_status = "Customer Booked Ticket"
    no_of_adult_tickets = request.form.get("no_of_adult_tickets")
    no_of_children_tickets = request.form.get("no_of_children_tickets")
    no_of_senior_citizen_tickets = request.form.get("no_of_senior_citizen_tickets")
    no_of_handy_capped_tickets = request.form.get("no_of_handy_capped_tickets")
    adult_amount = int(no_of_adult_tickets) * int(price_for_adults)
    children_amount = int(no_of_children_tickets) * int(price_for_children)
    senior_citizen_amount = int(no_of_senior_citizen_tickets) * int(price_for_senior_citizen)
    handy_capped_amount = int(no_of_handy_capped_tickets) * int(price_for_handy_capped)
    number_of_tickets = (int(no_of_adult_tickets) + int(no_of_children_tickets) + int(no_of_senior_citizen_tickets) + int(no_of_handy_capped_tickets))
    total_amount = int(adult_amount + children_amount + senior_citizen_amount + handy_capped_amount)
    adults = []
    for i in range(1, int(no_of_adult_tickets) + 1):
        namea = request.form.get("namea" + str(i))
        agea = request.form.get("agea" + str(i))
        adults.append({"name": namea, "age": agea})
    children = []
    for i in range(1, int(no_of_children_tickets) + 1):
        namec = request.form.get("namec" + str(i))
        agec = request.form.get("agec" + str(i))
        children.append({"name": namec, "age": agec})
    senior_citizen = []
    for i in range(1, int(no_of_senior_citizen_tickets) + 1):
        names = request.form.get("names" + str(i))
        ages = request.form.get("ages" + str(i))
        senior_citizen.append({"name": names, "age": ages})
    handy_capped = []
    for i in range(1, int(no_of_handy_capped_tickets) + 1):
        nameh = request.form.get("nameh" + str(i))
        ageh = request.form.get("ageh" + str(i))
        handy_capped.append({"name": nameh, "age": ageh})

    query = {"ticket_id": ObjectId(ticket_id), "stall_id": ObjectId(stall_id), "customer_id": ObjectId(customer_id), "date": date, "booking_status": booking_status, "booking_date": booking_date, "no_of_adult_tickets": no_of_adult_tickets, "adults": adults, "no_of_children_tickets": no_of_children_tickets, "children": children, "no_of_senior_citizen_tickets": no_of_senior_citizen_tickets, "senior_citizen": senior_citizen, "no_of_handy_capped_tickets": no_of_handy_capped_tickets, "handy_capped": handy_capped, "total_amount": total_amount, "number_of_tickets": number_of_tickets}
    result = booking_col.insert_one(query)
    booking_id = result.inserted_id
    query = {"_id": booking_id}
    booking = booking_col.find_one(query)
    number_of_tickets = booking['number_of_tickets']
    remaining_tickets = int(remaining_tickets) - int(number_of_tickets)
    query = {"_id": ObjectId(ticket_id)}
    query1 = {"$set": {"remaining_tickets": remaining_tickets}}
    ticket_col.update_one(query, query1)
    return render_template("pay_amount.html", booking=booking, get_ticket_id=get_ticket_id, get_stall_id=get_stall_id, get_customer_id=get_customer_id, str=str)


def get_ticket_id(ticket_id):
    query = {"_id": ObjectId(ticket_id)}
    ticket = ticket_col.find_one(query)
    return ticket


def get_customer_id(customer_id):
    query = {"_id": ObjectId(customer_id)}
    customer = customer_col.find_one(query)
    return customer


@app.route("/pay_amount1", methods=['post'])
def pay_amount1():
    customer_id = session['customer_id']
    booking_id = request.form.get("booking_id")
    total_amount = request.form.get("total_amount")
    card_number = request.form.get("card_number")
    holder_name = request.form.get("holder_name")
    expiry_date = request.form.get("expiry_date")
    status = "Transaction Successfully"
    date = datetime.now()
    query = {"customer_id": ObjectId(customer_id), "booking_id": ObjectId(booking_id), "total_amount": total_amount, "card_number": card_number, "holder_name": holder_name, "status": status, "expiry_date": expiry_date, "date": date}
    payment_col.insert_one(query)
    return render_template("message.html", message="Transaction Successfully", color="bg-success text-white")


@app.route("/view_entry_bookings")
def view_entry_bookings():
    query = {}
    ticket_id = request.args.get("ticket_id")
    if session['role'] == "Admin":
        query = {"ticket_id": ObjectId(ticket_id)}
    elif session['role'] == 'Customer':
        customer_id = session['customer_id']
        query = {"customer_id": ObjectId(customer_id), "ticket_id": ObjectId(ticket_id)}
    bookings = booking_col.find(query)
    today = datetime.now()
    return render_template("view_entry_bookings.html", today=today, bookings=bookings, get_ticket_id=get_ticket_id, get_stall_id=get_stall_id, get_customer_id=get_customer_id)


@app.route("/view_booked_tickets")
def view_booked_tickets():
    query = {}
    ticket_id = request.args.get("ticket_id")
    booking_id = request.args.get("booking_id")
    if session['role'] == "Admin":
        query = {"_id": ObjectId(booking_id)}
    elif session['role'] == 'Customer':
        customer_id = session['customer_id']
        query = {"customer_id": ObjectId(customer_id), "_id": ObjectId(booking_id)}
    bookings = booking_col.find(query)
    return render_template("view_booked_tickets.html", bookings=bookings, get_ticket_id=get_ticket_id, get_stall_id=get_stall_id)


@app.route("/view_payments")
def view_payments():
    query = {}
    if session['role'] == "Admin":
        ticket_id = request.args.get("ticket_id")
        query = {"ticket_id": ObjectId(ticket_id)}
        bookings = booking_col.find(query)
        booking_ids = []
        for booking in bookings:
            booking_ids.append({"booking_id": booking['_id']})
            query = {"$or": booking_ids}
    elif session['role'] == "Customer":
        customer_id = session['customer_id']
        query = {"customer_id": ObjectId(customer_id)}
    payments = payment_col.find(query)
    return render_template("view_payments.html", payments=payments, get_customer_id=get_customer_id)


@app.route("/cancel_booking")
def cancel_booking():
    booking_id = request.args.get("booking_id")
    query = {"booking_id": ObjectId(booking_id)}
    payment = payment_col.find_one(query)
    payment_id = payment['_id']
    amount = payment['total_amount']
    date = datetime.now()
    customer_id = session['customer_id']
    status = "Amount Credited to Customer"
    query = {"payment_id": ObjectId(payment_id), "amount": amount, "date": date, "customer_id": ObjectId(customer_id), "status": status}
    refunds_col.insert_one(query)
    query = {"_id": ObjectId(booking_id)}
    query2 = {"$set": {"booking_status": "Customer Booking Cancelled"}}
    booking_col.update_one(query, query2)
    query = {"_id": ObjectId(payment_id)}
    query2 = {"$set": {"status": "Amount Refunded to Customer"}}
    payment_col.update_one(query, query2)
    return render_template("message.html", message="Amount Credited to Customer", color="bg-success text-white")


def get_payment_by_refund(payment_id):
    query = {"_id": ObjectId(payment_id)}
    payment = payment_col.find_one(query)
    return payment


@app.route("/view_refund_history")
def view_refund_history():
    payment_id = request.args.get("payment_id")
    query = {"payment_id": ObjectId(payment_id)}
    refund = refunds_col.find_one(query)
    return render_template("view_refund_history.html", refund=refund, get_payment_by_refund=get_payment_by_refund, get_customer_id=get_customer_id)


def available_tickets(ticket_id):
    query = {"ticket_id": ObjectId(ticket_id)}
    bookings = booking_col.find(query)
    number_of_booked_tickets = 0
    for booking in bookings:
        number_of_booked_tickets = booking['number_of_tickets']

    query = {"_id": ObjectId(ticket_id)}
    ticket = ticket_col.find_one(query)
    remaining_tickets = ticket['remaining_tickets']
    available_tickets = int(remaining_tickets) - int(number_of_booked_tickets)

    return available_tickets


@app.route("/logout")
def logout():
    session.clear()
    return render_template("home.html")


if __name__ == "__main__":
    app.run(debug=True)