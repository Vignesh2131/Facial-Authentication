#OS operations - read and write
import os.path
import os
import requests
#Date time
import datetime
import time
#Interface
import tkinter as tk
import util
#Cloudinary
import cloudinary
import cloudinary.uploader
import cloudinary.api
#face
import cv2
from PIL import Image, ImageTk
#SQL Server
import mysql.connector
#Email automation
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
#Parallel Programming
import threading
import subprocess
import base64

class PostLoginWindow:
    def __init__(self, name, db_path,path, app_instance):
        self.path = path
        self.name = name
        self.db_path = db_path
        self.app_instance = app_instance

        self.window = tk.Toplevel()
        self.window.geometry("1200x520+350+100")
        self.window.title("Verification 2")

        self.label = tk.Label(self.window, text=f"Enter your VoterID")
        self.label.config(font=("Helvetica", 20))
        self.label.pack(pady=20)

        self.input_text = util.get_entry_text(self.window)
        self.input_text.pack(pady=10)

        self.verify_button = util.get_button(self.window, "Verify", "green", self.verify)
        self.verify_button.pack(pady=10)  

    def verify(self):
        input_name = self.input_text.get(1.0, "end-1c").strip()

        if input_name == self.name:
            db_connection = mysql.connector.connect(
                host='127.0.0.1',
                user='root',
                password='Vignesh@21',
                database='test'
            )
            cursor = db_connection.cursor()
            # Check if the unique id exists in the database
            cursor.execute("SELECT image FROM voters WHERE voterId = %s", (self.name,))
            user = cursor.fetchone()
            if user:
                # Extract public ID from the image URL (assuming Cloudinary URL format)
                image = user[0]
                public_id = image.split("/")[-1].split(".")[0]
                print(public_id)
                self.app_instance.verified_count += 1
                self.app_instance.update_counts_labels()
                # Delete image from Cloudinary
                cloudinary.api.delete_resources([f"voters/{public_id}"],resource_type="image", type="upload")
                #adding verified user to verify db
                cursor.execute("INSERT INTO verifieddata (voterId, timeLogged) VALUES (%s, %s)",
                               (self.name, datetime.datetime.now()))
                # Delete user's data from the database
                cursor.execute("DELETE FROM voters WHERE voterId = %s", (self.name,))
                db_connection.commit()
                db_connection.close()  # Close the database connection
                self.window.destroy()  # Close the verification window
                util.msg_box("Success", "Verification Successful!")
            else:

                self.app_instance.non_verified_count += 1
                self.app_instance.update_counts_labels()
                # upload_result = cloudinary.uploader.upload(self.path, folder="nonVerifiedVoters", public_id=self.name,
                #                                            format='jpg')
                os.remove(os.path.join(self.db_dir, '{}.jpg'.format(input_name)))
                util.msg_box("Error", "Unauthorized Voter")

        else:
            self.app_instance.non_verified_count += 1
            self.app_instance.update_counts_labels()
            util.msg_box("Error", "Verification Failed!")


class App:
    def __init__(self):
        self.verified_count = 0
        self.non_verified_count = 0
        self.vote_percentage = 0.0
        self.total_voters = 20
        self.booth_name = "GCET Cheeryal"


        if __name__ == '__main__':
            self.main_window = tk.Tk() #Variable representing the window
            self.main_window.geometry("1920x1080")
            self.main_window.title("Verification 1")

            self.vote_percentage = tk.Label(self.main_window,
                                                     text=f"Vote Percentage: {self.vote_percentage} %",
                                                     bg="Yellow",
                                                     fg="black")
            self.vote_percentage.config(font=("Helvetica", 40))
            self.vote_percentage.pack(pady=15)
            self.vote_percentage.place(x=750, y=100)

            self.booth_name = tk.Label(self.main_window,
                                            text=f"Booth name: {self.booth_name}",
                                            fg="black")
            self.booth_name.config(font=("Helvetica", 30))
            self.booth_name.pack(pady=15)
            self.booth_name.place(x=750, y=200)

            self.verified_count_label = tk.Label(self.main_window, text=f"Verified Voters: {self.verified_count}",bg="green", fg="white")
            self.verified_count_label.config(font=("Helvetica", 40))
            self.verified_count_label.pack(pady=15)
            self.verified_count_label.place(x=50, y=600)

            self.non_verified_count_label = tk.Label(self.main_window, text=f"Non-Verified Voters: {self.non_verified_count}",bg="red", fg="white")
            self.non_verified_count_label.config(font=("Helvetica", 40))
            self.non_verified_count_label.pack(pady=15)
            self.non_verified_count_label.place(x=50, y=700)



            self.login_button_main_window = util.get_button(self.main_window, 'Verify', 'blue', self.login)
            self.login_button_main_window.place(x=750, y=300)

            self.register_new_user_button_main_window = util.get_button(self.main_window, 'register new Voter', 'gray',
                                                                        self.register_new_user, fg='black')
            self.register_new_user_button_main_window.place(x=750, y=400)

            self.webcam_label = util.get_img_label(self.main_window)
            self.webcam_label.place(x=10, y=0, width=700, height=500)

            self.add_webcam(self.webcam_label)

            #SQL Connection
            self.db_connection = mysql.connector.connect(
                host='127.0.0.1',
                user='root',
                password='Vignesh@21',
                database='test'
            )

            self.db_dir = './db'
            if not os.path.exists(self.db_dir):
                os.mkdir(self.db_dir)

            self.log_path = './log.txt'
            self.download_images_from_cloudinary()
            email_thread = threading.Thread(target=self.send_emails_thread)
            email_thread.daemon = True
            email_thread.start()

    def add_webcam(self, label):
        if 'cap' not in self.__dict__:
            self.cap = cv2.VideoCapture(0)

        self._label = label
        self.process_webcam()

    def process_webcam(self):
        ret, frame = self.cap.read()

        if ret:  # Check if frame is properly captured
            self.most_recent_capture_arr = frame
            img_ = cv2.cvtColor(self.most_recent_capture_arr, cv2.COLOR_BGR2RGB) # Black and White
            self.most_recent_capture_pil = Image.fromarray(img_) #vector value
            imgtk = ImageTk.PhotoImage(image=self.most_recent_capture_pil) #Length conversion
            self._label.imgtk = imgtk
            self._label.configure(image=imgtk)
        else:
            print("Error: Failed to capture frame from webcam.")

        self._label.after(20, self.process_webcam)

    def login(self):
       unknown_img_path = './.tmp.jpg'
       cv2.imwrite(unknown_img_path,self.most_recent_capture_arr) #recent face processing
       output =str(subprocess.check_output(['face_recognition',self.db_dir,unknown_img_path]))
       name = output.split(',')[1][:-5]
       if name in ['unknown_person','no_persons_found','name'+'\r\n']:
           upload_result = cloudinary.uploader.upload(unknown_img_path, folder="nonVerifiedVoters", public_id=name, format='jpg')
           self.non_verified_count += 1
           self.update_counts_labels()
           util.msg_box('Error...','Face is not Unauthorized.')
       else:
           util.msg_box('Verification 1 Successful', 'Face is Authorized.')
           post_login_window = PostLoginWindow(name, self.db_dir, unknown_img_path, self)
           self.main_window.wait_window(post_login_window.window)
           with open(self.log_path, 'a') as f:
               f.write('{},{}\n'.format(name, datetime.datetime.now()))
       os.remove(unknown_img_path)

    def update_counts_labels(self):
        # Update text of count labels
        self.verified_count_label.config(text="Verified Count: {}".format(self.verified_count))
        self.non_verified_count_label.config(text="Non-Verified Count: {}".format(self.non_verified_count))
        self.vote_percentage.config(text="Vote percentage: {}".format((self.verified_count/self.total_voters)*100))

    def register_new_user(self):
        self.register_new_user_window = tk.Toplevel(self.main_window)
        self.register_new_user_window.attributes("-fullscreen", True)
        self.main_window.title("Registering the User")

        self.accept_button_register_new_user_window = util.get_button(self.register_new_user_window, 'Accept', 'green',
                                                                      self.accept_register_new_user)
        self.accept_button_register_new_user_window.place(x=750, y=500)

        self.try_again_button_register_new_user_window = util.get_button(self.register_new_user_window, 'Try again',
                                                                         'red', self.try_again_register_new_user)
        self.try_again_button_register_new_user_window.place(x=1150, y=500)

        self.capture_label = util.get_img_label(self.register_new_user_window)
        self.capture_label.place(x=10, y=0, width=700, height=500)

        self.add_img_to_label(self.capture_label)

        self.entry_text_register_new_user = util.get_entry_text(self.register_new_user_window)
        self.entry_text_register_new_user.place(x=750, y=150)

        self.text_label_register_new_user = util.get_text_label(self.register_new_user_window,
                                                                'Please, \nEnter Voter Id:')
        self.text_label_register_new_user.place(x=750, y=70)

        self.entry_text_name_register_new_user = util.get_entry_text(self.register_new_user_window)
        self.entry_text_name_register_new_user.place(x=750, y=350)

        self.text_label_name_register_new_user = util.get_text_label(self.register_new_user_window,
                                                                     'Enter Name:')
        self.text_label_name_register_new_user.place(x=750, y=300)

    def try_again_register_new_user(self):
        self.register_new_user_window.destroy()

    def add_img_to_label(self,label):
        imgtk = ImageTk.PhotoImage(image=self.most_recent_capture_pil)
        label.imgtk = imgtk
        label.configure(image=imgtk)
        self.register_new_user_capture = self.most_recent_capture_arr.copy()

    def start(self):
        self.main_window.mainloop()

    def accept_register_new_user(self):
        name = self.entry_text_register_new_user.get(1.0, "end-1c") # data of input field
        user_name = self.entry_text_name_register_new_user.get(1.0, "end-1c")
        _, image_encoded = cv2.imencode('.jpg', self.register_new_user_capture)
        image_bytes = image_encoded.tobytes()
        image_encoded_str = base64.b64encode(image_encoded).decode('utf-8')
         # Upload image to Cloudinary as JPG
        upload_result = cloudinary.uploader.upload(image_bytes,folder="voters", public_id=name, format='jpg')
        # Get the URL of the uploaded image from Cloudinary
        image_url = upload_result['secure_url']
        cv2.imwrite(os.path.join(self.db_dir,'{}.jpg'.format(name)),self.register_new_user_capture)
        cursor = self.db_connection.cursor()
        # Insert user information into the database
        cursor.execute("INSERT INTO voters (voterId,name, image ,vector) VALUES (%s, %s, %s, %s)", (name,user_name, image_url, image_encoded_str))
        self.db_connection.commit()
        util.msg_box('Success!', 'User was registered successfully !')
        self.register_new_user_window.destroy()

    def send_emails_thread(self):
        while True:
            send_email(self.verified_count, self.non_verified_count, self.booth_name , self.total_voters)
            time.sleep(120)

    def download_images_from_cloudinary(self):
        # Create the local directory if it doesn't exist
        if not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)
        else:
            # Clear the existing files in the directory
            file_list = os.listdir(self.db_dir)
            for file_name in file_list:
                os.remove(os.path.join(self.db_dir, file_name))
        # Get all resources (images) from the "voters" folder in Cloudinary
        resources = cloudinary.api.resources(type='upload', prefix='voters/')['resources']

        # Download each image to the local directory
        for resource in resources:
            image_url = resource['secure_url']
            image_name = os.path.basename(image_url)
            local_path = os.path.join(self.db_dir, image_name)

            # Download the image
            response = requests.get(image_url)
            with open(local_path, 'wb') as f:
                f.write(response.content)


def send_email(verified_count ,non_verified_count ,booth_name ,total_voters):
    # Email configurations
    sender_email = "vigneshsadhu143@gmail.com"
    receiver_email = "vigneshsadhu506@gmail.com"
    password = "wkzz osfm yfte losb"

    # Create message container
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = f"Voting Count Update"

    # Email body
    c = datetime.datetime.now()
    current_time = c.strftime('%H:%M:%S')
    body = f"Verified Count: {verified_count}\nNon-Verified Count: {non_verified_count}\nTime: {current_time}\nVote percentage: {(verified_count/total_voters)*100}\n Booth Name: GCET Cheeryal"
    msg.attach(MIMEText(body, 'plain'))

    # Send email
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender_email, password)
        server.send_message(msg)


if __name__=="__main__":
    cloudinary.config(
        cloud_name="dupjk8tlb",
        api_key="255112319479189",
        api_secret="eU50509ZQDtDjQXHtb3nbrn3c6E"
    )
    app = App()
    app.start()

