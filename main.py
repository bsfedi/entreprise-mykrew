from fastapi import FastAPI,Request,HTTPException
import uvicorn 
from fastapi.middleware.cors import CORSMiddleware
import stripe
from pymongo import MongoClient
from pymongo.database import Database
from bson import  ObjectId
from datetime import date, datetime
from fastapi import UploadFile
from pydantic import BaseModel, EmailStr
from typing import Optional
import subprocess


from bson import ObjectId
from fastapi import APIRouter, File, HTTPException
from argon2 import PasswordHasher
import re
import smtplib

user_router = APIRouter(tags=["User"])

ph = PasswordHasher()

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
gmail_user = "fedislimen98@gmail.com"
pass_code=  "wiuijqbeodgezebw"


import random
import string
subject = f"Compte créé sur la plateforme Mykrew"
def generate_password(length=12):
    # Define the characters to choose from
    characters = string.ascii_letters + string.digits + string.punctuation
    
    # Generate the password
    password = ''.join(random.choice(characters) for i in range(length))
    
    return password


class entreprise(BaseModel):
    name: str =""
    siret: str =""
    secteur : str =""
    taille : str  =""
    adresse : str =""
    site_web : Optional[str] = "" 
    nom: str
    prenom : str
    fonction : str
    email : str
    phone : str








db : Database = MongoClient("mongodb://root:root@152.228.135.170:27017/")["myKrew"]

app=FastAPI()
stripe.api_key = "sk_test_51Konz7AH2X0tC2h7ISzXJXqRwx85OPqhCLPZgxPgUSLEU1BUlHo4e5kF0w0TCItFD8xp94YnERfOGHsAS7D4eLs5001bHenXDy"

import random



@app.post("/add_entreprise")
async def add_entreprise(entreprise: entreprise):
    
    check_ports= []
    new_entreprise = db['entreprise'].insert_one(entreprise.dict())
    all_ports = db["prots"].find()
    for port in all_ports :
        check_ports.append(port['front'])
        check_ports.append(port['back'])

    back = random.randint(1000, 9999)
    front = random.randint(10, 99)

    while back in check_ports or front  in check_ports  :
        
        back = random.randint(1000, 9999)
        front = random.randint(10, 99)
    else:
     
        all_ports = db["prots"].insert_one({"entreprise":new_entreprise.inserted_id,"front":front,"back":back})

    # Run the shell command

    try:
        command = ["./docker.sh", f"{back}", f"{entreprise.name.lower()}", f"mongodb://root:root@152.228.135.170:27017/{entreprise.name.lower()}?authSource=admin", f"{entreprise.name.lower()}", f"{front}", f"http://152.228.135.170:{back}/"]
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        add_user(entreprise)
        return f"http://152.228.135.170:{front}/"
    except subprocess.CalledProcessError as e:
        return {"message": "Entreprise added, but script failed!", "error": e.stderr.decode()}


@app.get("/change_status/{entreprise_id}/{status}")
async def change_status_container(entreprise_id: str,status:str):
    entreprise = db['entreprise'].find_one({'_id': ObjectId(entreprise_id)})
    if not entreprise:
        return {"error": "Entreprise not found"}

    try:

        if status == 'False':
            # Find backend container name
            backend_command = [
                "docker", "ps", 
                "--filter", f"ancestor=mykrew-backend_{entreprise['name'].lower()}", 
                "--format", "{{.Names}}"
            ]
            backend_result = subprocess.run(backend_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            backend_name = backend_result.stdout.strip()

            # Find frontend container name
            frontend_command = [
                "docker", "ps", 
                "--filter", f"ancestor={entreprise['name'].lower()}", 
                "--format", "{{.Names}}"
            ]
            frontend_result = subprocess.run(frontend_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            frontend_name = frontend_result.stdout.strip()
            if backend_name:
                # Stop backend container
                subprocess.run(["docker", "stop", backend_name], check=True)
            if frontend_name:
                # Stop frontend container
                subprocess.run(["docker", "stop", frontend_name], check=True)
            db["entreprise"].update_one(
            {"_id": ObjectId(entreprise_id)},
            {
                "$set": {
                    "instance_status": "stopped"
                }
            },
            )
        else:
            # Find backend container name
            backend_command = [
                "docker", "ps", "-a", 
                "--filter", f"name=mykrew-backend_{entreprise['name'].lower()}", 
                "--format", "{{.Names}}"
            ]
            backend_result = subprocess.run(backend_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            backend_name = backend_result.stdout.strip()

            # Find frontend container name
            frontend_command = [
                "docker", "ps", "-a", 
                "--filter", f"ancestor={entreprise['name'].lower()}", 
                "--format", "{{.Names}}"
            ]
            frontend_result = subprocess.run(frontend_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            frontend_name = frontend_result.stdout.strip()

            if backend_name:
                # Start backend container
                subprocess.run(["docker", "start", backend_name], check=True)
            if frontend_name:
                # Start frontend container
                subprocess.run(["docker", "start", frontend_name], check=True)
            db["entreprise"].update_one(
            {"_id": ObjectId(entreprise_id)},
            {
                "$set": {
                    "instance_status": "started"
                }
            },
            )
        return {"message": f"Containers for entreprise '{entreprise['name']}' have been stopped successfully"}

    except subprocess.CalledProcessError as e:
        return {"error": "Failed to stop containers", "details": e.stderr}


def add_user(entreprise):
    """
    Validates a password format based on specified requirements:
    - At least 8 characters long
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one digit
    - Contains at least one special character
    """
    # Get date of today

    try:
        
       
        sender_address = gmail_user
        sender_pass = pass_code
        receiver_address = entreprise.email
        message = MIMEMultipart()
        message["From"] = sender_address
        message["To"] = entreprise.email
        message["Subject"] = subject

                            # Attach the additional information and HTML table to the email
        message.attach(MIMEText(f" Bonjour, Pour y accéder au platforme, veuillez utiliser les paramètres suivants:  <br>   Nom d’utilisateur : <b> {entreprise.email} </b> <br> <b> Mot de passe: 123456 </b> <br> En cas de difficultés, vous pouvez contacter l’administrateur de la plateforme via mail ou par téléphone.  ", "html"))

                            # Create SMTP session for sending the mail
        session = smtplib.SMTP("smtp.gmail.com", 587)  # use gmail with port
        session.starttls()  # enable security
        session.login(sender_address, sender_pass)  # login with mail_id and password
        text = message.as_string()
        db : Database = MongoClient("mongodb://root:root@152.228.135.170:27017/")[f"{entreprise.name.lower()}"]
        response = db["users"].insert_one({
            "image": "default.jpg",
            "email": entreprise.email,
            "password": "$2b$10$ICWgDd25cMt72MgRPSwLA.9N6VpD2MxcOxxfYBmxwUhGUn.PeJ82W",
            "role": "ADMIN",
            "missions": [],
            "userDocuments": [],
            "__v": 0,
            "personalInfo": {
                "firstName": entreprise.nom,
                "lastName": entreprise.prenom,
                "email": entreprise.email,
                "location": "",
                "nationality": "",
                "phoneNumber": entreprise.phone
            },
            "isAvtivated": True
            })
        if response.inserted_id :
            session.sendmail(sender_address, receiver_address, text)
        else:
            session.sendmail(sender_address, receiver_address, "please contact us if you receive this mail")

        return {"response":"user added sucessfully"}
    except Exception as e:
        return {"error": str(e)}
    

@app.get("/create-checkout-session/{entreprise_id}/{price_id}")
async def create_checkout_session(entreprise_id,price_id):
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        metadata={
            'entreprise_id': entreprise_id,
            'price_id':price_id
        },
        line_items=[
            {
                "price": price_id,
                "quantity": 1,
            }
        ],
        mode="subscription",
        success_url="https://app.easy-bq.com/settings",
        # customer=customer_id,  # Pass the customer ID
    )
    return {"session_url": session.url}


@app.get('/nb_instances')
async def get_nb_instances():
    total_entreprises = db['entreprise'].count_documents({})
    all_entreprise = db['entreprise'].find()
    
    total_consultants = 0
    
    for entreprise in all_entreprise:
        entreprise['_id'] = str(entreprise['_id'])
        db_name = entreprise['name'].lower()  # Convert the name to lowercase
        total_consultant = client[db_name]['users'].count_documents({})
        entreprise['total_consultant'] = total_consultant
        
        total_consultants += total_consultant
    
    return {"total_entreprises": total_entreprises, "total_consultants": total_consultants}


from asyncio import Queue

# Initialize event queue
event_queue = Queue()

import json

@app.post("/webhook/stripe")
async def webhook(request: Request):
    endpoint_secret = "whsec_2gmhJrNgO68npQZCVlS0NcbxhqSVyPXq"
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")
    # Decode the payload from bytes to string
    payload_str = payload.decode('utf-8')

    # Parse the JSON string
    payload_json = json.loads(payload_str)

    if payload_json["type"] == "checkout.session.completed":
        entreprise_id = payload_json["data"]["object"]["metadata"]["entreprise_id"]
        price_id = payload_json["data"]["object"]["metadata"]["price_id"]

      
        transaction_data = {
            "payment_status": "success",
        }
        db["entreprise"].update_one(
            {"_id": ObjectId(entreprise_id)},
            {
                "$set": transaction_data
            },
        )
        package = db["packages"].find({"price_id": price_id})

        for data in package:
            nb_preregister = data['pre_register']
            db["entreprise"].update_one(
                {"_id": ObjectId(entreprise_id)},
                {
                    "$set": {
                        "nb_preregister": nb_preregister,
                        "package_id": price_id,
                    }
                },
            )

        return "OK"

# Initialize the MongoDB client once
client = MongoClient("mongodb://root:root@152.228.135.170:27017/")

@app.get('/get_entreprises')
async def get_entreprises():
    entreprises = []
    all_entreprise = db['entreprise'].find()
    for entreprise in all_entreprise:
        entreprise['_id'] = str(entreprise['_id'])
        db_name = entreprise['name'].lower()  # Convert the name to lowercase
        total_consultant = client[db_name]['users'].count_documents({})
        entreprise['total_consultant'] = total_consultant
        entreprises.append(entreprise)
    return entreprises
# @app.post('/webhook/stripe')
# async def stripe_webhook(request: Request):
#     # Parse the JSON payload from the request
    
#     endpoint_secret = "we_1Oj5fKAH2X0tC2h7Patfnzkz"
#     payload = await request.json()
#     print(payload['type'])
#     sig_header = request.headers.get("Stripe-Signature")
    
#     entreprise_id = None  # Define entreprise_id before the if statement

#     if payload['type'] == "checkout.session.completed":
#         subscription_id = payload['data']['object']['subscription']
#         entreprise_id = payload['data']['object']['metadata']['entreprise_id']
#         db["entreprise"].update_one(
#             {"_id": ObjectId(entreprise_id)},
#             {
#                 "$set": {
#                     "subscription_id": subscription_id,
#                     "payment_status": "success",
#                 }
#             },
#         )

#     elif payload['type'] == "customer.subscription.created" or payload['type'] == "customer.subscription.updated":
#         # Check if there are pending checkout sessions for the same customer
#         pending_sessions = db["pending_checkout_sessions"].find({"customer_id": payload['data']['object']['customer']})
        
#         for session in pending_sessions:
#             subscription_id = session['subscription_id']
#             # Update the subscription status
#             db["entreprise"].update_one(
#                 {"_id": ObjectId(entreprise_id)},
#                 {
#                     "$set": {
#                         "subscription_id": subscription_id,
#                     }
#                 },
#             )
            
#             package = db["packages"].find({"price_id": session['price_id']})
#             for data in package:
#                 nb_preregister = data['pre_register']
#                 db["entreprise"].update_one(
#                     {"subscription_id": subscription_id},
#                     {
#                         "$set": {
#                             "nb_preregister": nb_preregister,
#                             "package_id": session['price_id'],
#                         }
#                     },
#                 )

#         # Remove the pending checkout sessions
#         db["pending_checkout_sessions"].delete_many({"customer_id": payload['data']['object']['customer']})

#     else:
#         # Handle other webhook events here
#         pass

@app.get('/get_packages')
def get_all_users():
    packages = []
    try:
        for pack in db["packages"].find():
            print(pack)
            # Convert ObjectId to string
            pack["_id"] = str(pack["_id"])

            packages.append(pack)  # Append user object to user_list
            print(packages)
        return packages  # Return the list of users
    except Exception as ex:
        return {
            "message": f"{str(ex)}"
        }  # Return an error message with exception details if an exception occurs


@app.post('/post-pre-register')
async def add_preregister(entreprise_id,preregister):
    db["entreprise"].find_one({"_id": ObjectId(entreprise_id)})

""" allows a server to indicate any origins (domain, scheme, or port) """
origins = ["*"]
app.add_middleware(CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
if __name__ == '__main__':
    uvicorn.run(app="main:app",host="0.0.0.0",port=5200,reload=True)