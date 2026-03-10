from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from .models import UserSession, Area, Turf, Booking
from datetime import datetime, timedelta
import requests
import json


ACCESS_TOKEN = "EAAM2919mn8MBQ8nUiwytTn3qgtNUnN6x9ovBxzHXbOOAXXuQlrOICdNHTbGHtniZBiRy79PMrni0GUJvvsqVAedsGFhFwsm062qFFCZCJEBhNEYInuwSIpO9jPqy2o6tq1qwh8l5tSvBixbuF77ddipWdfZA53VtoJJFjC3VRmA5s03BHscxuulEKKdO9taww2E5uIEhKpDYLYJW8hVuVuaGZCLcxyZAvErCMkqI7Q978yMY1AZCn72CSq2gfv0K4h2O4UuDHysGBy2goRJxkN"
PHONE_NUMBER_ID = "1093835477138219"
VERIFY_TOKEN = "turfbot123"


SLOTS = [
    "6:00 AM - 7:00 AM",
    "7:00 AM - 8:00 AM",
    "8:00 AM - 9:00 AM",
    "6:00 PM - 7:00 PM",
    "7:00 PM - 8:00 PM",
]


def send_whatsapp(phone, message):

    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {"body": message}
    }

    requests.post(url, headers=headers, json=payload)


@csrf_exempt
def whatsapp_webhook(request):

    if request.method == "GET":

        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            return HttpResponse(challenge)

        return HttpResponse("Verification failed")


    if request.method == "POST":

        data = json.loads(request.body)

        try:

            message = data["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"]
            phone = data["entry"][0]["changes"][0]["value"]["messages"][0]["from"]

            incoming_msg = message.strip()

            session, _ = UserSession.objects.get_or_create(phone_number=phone)

            if not session.step:
                session.step = "search"
                session.save()


            # START
            if incoming_msg.lower() == "start":

                session.step = "search"
                session.selected_area = None
                session.selected_turf = None
                session.selected_date = None
                session.selected_slot = None
                session.save()

                send_whatsapp(phone, "👋 Welcome to TurfBot\n\nType your Area name or Turf name")
                return JsonResponse({"status": "ok"})


            # SEARCH AREA / TURF
            if session.step == "search":

                turf_obj = Turf.objects.filter(name__iexact=incoming_msg).first()

                if turf_obj:

                    session.selected_area = turf_obj.area.name
                    session.selected_turf = turf_obj.name
                    session.step = "date"
                    session.save()

                else:

                    area_obj = Area.objects.filter(name__iexact=incoming_msg).first()

                    if area_obj:

                        session.selected_area = area_obj.name
                        session.step = "turf_list"
                        session.save()

                        turfs = Turf.objects.filter(area=area_obj)

                        text = f"🏟 Turfs in {area_obj.name}\n\n"

                        for i, turf in enumerate(turfs, start=1):
                            text += f"{i}. {turf.name}\n"

                        text += "\nReply with turf number"

                        send_whatsapp(phone, text)
                        return JsonResponse({"status": "ok"})

                    send_whatsapp(phone, "❌ Area or Turf not found")
                    return JsonResponse({"status": "ok"})


            # TURF SELECT
            if session.step == "turf_list":

                turfs = list(Turf.objects.filter(area__name=session.selected_area))

                index = int(incoming_msg) - 1

                session.selected_turf = turfs[index].name
                session.step = "date"
                session.save()


            # DATE PICKER
            if session.step == "date":

                today = datetime.today().date()

                text = f"📅 Select Date – {session.selected_turf}\n\n"

                for i in range(7):
                    next_date = today + timedelta(days=i)
                    text += f"{i+1}. {next_date.strftime('%d %b %Y')}\n"

                text += "\nReply with date number\nType 0 to go back"

                session.step = "date_select"
                session.save()

                send_whatsapp(phone, text)
                return JsonResponse({"status": "ok"})


            # DATE SELECT
            if session.step == "date_select":

                if incoming_msg == "0":

                    session.step = "search"
                    session.save()

                    send_whatsapp(phone, "Type your Area name or Turf name")
                    return JsonResponse({"status": "ok"})


                index = int(incoming_msg) - 1

                session.selected_date = datetime.today().date() + timedelta(days=index)
                session.step = "slot"
                session.save()


            # SLOT LIST
            if session.step == "slot":

                booked_slots = Booking.objects.filter(
                    turf=session.selected_turf,
                    date=session.selected_date
                )

                text = f"🕒 Available Slots\n"
                text += f"📅 {session.selected_date.strftime('%d %b %Y')}\n\n"

                for i, slot in enumerate(SLOTS, start=1):

                    is_booked = False

                    for booking in booked_slots:
                        if slot in booking.slot.split(","):
                            is_booked = True

                    if is_booked:
                        text += f"{i}. ❌ {slot}\n"
                    else:
                        text += f"{i}. ✅ {slot}\n"

                text += "\nReply with slot numbers (Example: 1 or 1,2)\nType 0 to go back"

                session.step = "slot_select"
                session.save()

                send_whatsapp(phone, text)
                return JsonResponse({"status": "ok"})


            # SLOT SELECT
            if session.step == "slot_select":

                if incoming_msg == "0":

                    session.step = "date"
                    session.save()
                    return JsonResponse({"status": "ok"})


                slot_numbers = [x.strip() for x in incoming_msg.split(",")]

                indexes = sorted([int(num) - 1 for num in slot_numbers])

                selected_slots = [SLOTS[i] for i in indexes]

                session.selected_slot = ",".join(selected_slots)
                session.step = "confirm_booking"
                session.save()

                slot_display = "\n".join(selected_slots)

                text = (
                    f"⚠ Confirm Booking?\n\n"
                    f"🏟 {session.selected_turf}\n"
                    f"📅 {session.selected_date.strftime('%d %b %Y')}\n"
                    f"🕒 {slot_display}\n\n"
                    "Reply YES to confirm\n"
                    "Reply NO to change slot"
                )

                send_whatsapp(phone, text)
                return JsonResponse({"status": "ok"})


            # CONFIRM BOOKING
            if session.step == "confirm_booking":

                if incoming_msg.lower() == "yes":

                    Booking.objects.create(
                        area=session.selected_area,
                        turf=session.selected_turf,
                        date=session.selected_date,
                        slot=session.selected_slot,
                        phone_number=session.phone_number
                    )

                    turf_obj = Turf.objects.get(name=session.selected_turf)
                    owner_phone = turf_obj.owner_phone

                    owner_message = (
                        f"📢 New Booking\n\n"
                        f"Turf: {session.selected_turf}\n"
                        f"Area: {session.selected_area}\n"
                        f"Date: {session.selected_date}\n"
                        f"Slots: {session.selected_slot}\n"
                        f"Customer: {session.phone_number}"
                    )

                    send_whatsapp(turf_obj.owner_phone, owner_message)

                    session.step = "search"
                    session.save()

                    send_whatsapp(phone, "✅ Booking Confirmed!\n\nType START to book again")

                    return JsonResponse({"status": "ok"})


                if incoming_msg.lower() == "no":

                    session.step = "slot"
                    session.save()

                    return JsonResponse({"status": "ok"})


            send_whatsapp(phone, "Type START to begin")

        except Exception as e:

            print("Error:", e)

        return JsonResponse({"status": "received"})