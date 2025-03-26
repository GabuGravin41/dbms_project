import MySQLdb
import pandas as pd
import json
import xml.etree.ElementTree as ET

# Database Configuration
db = MySQLdb.connect(
    host="localhost",
    user="root",
    passwd="dalton",
    db="new_mydb",
    charset="utf8"
)
cursor = db.cursor()

def get_booking(booking_id):
    # Query the database for a specific booking
    query = 'SELECT * FROM booking WHERE booking_id = %s'
    cursor.execute(query, (booking_id,))
    result = cursor.fetchone()

    if result:
        # Convert the result to a dictionary
        booking_data = {
            'id': result[0],
            'customer_name': result[1],
            'booking_date': result[2],
            'status': result[3],
            # Add other fields as necessary
        }
        return booking_data
    else:
        return None

def save_as_json(data, filename='booking.json'):
    with open(filename, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def save_as_xml(data, filename='booking.xml'):
    root = ET.Element("booking")
    for key, value in data.items():
        child = ET.SubElement(root, key)
        child.text = str(value)

    tree = ET.ElementTree(root)
    tree.write(filename)

# Example usage
booking_id = 1  # Replace with the desired booking ID
booking_data = get_booking(booking_id)

if booking_data:
    print("Booking Data:", booking_data)
    
    # Save as JSON
    save_as_json(booking_data)
    print("Data saved as JSON.")

    # Save as XML
    save_as_xml(booking_data)
    print("Data saved as XML.")
else:
    print("Booking not found.")

# Close the connection  
db.close()
