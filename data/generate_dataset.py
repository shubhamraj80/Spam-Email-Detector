"""
Dataset generator for spam/ham email classification.
Creates a balanced CSV dataset with realistic examples.
"""

import csv
import random

spam_samples = [
    "Congratulations! You've won a $1,000,000 lottery prize. Click here to claim now!",
    "FREE iPhone giveaway! You have been selected. Act now before offer expires!",
    "URGENT: Your bank account has been compromised. Verify your details immediately.",
    "Make money fast! Work from home and earn $5000 per week. No experience needed!",
    "You are the lucky winner! Send us your credit card details to receive your prize.",
    "LIMITED TIME OFFER: Buy Viagra online at 80% discount. No prescription needed!",
    "Dear friend, I am a Nigerian prince and I need your help to transfer $10 million.",
    "Click here to enlarge and satisfy your partner. Guaranteed results in 3 days!",
    "Lose 30 pounds in 30 days with this miracle pill! Doctors hate this secret.",
    "WARNING: Your computer has a virus. Call 1-800-XXX-XXXX immediately to fix it.",
    "Get rich quick scheme revealed! Make thousands daily from home. 100% guaranteed.",
    "Cheap medication online! Buy Xanax, Valium, Oxycodone without prescription.",
    "You have been pre-approved for a $50,000 loan. No credit check required!",
    "Act now! This investment opportunity will make you a millionaire overnight.",
    "CLAIM YOUR FREE GIFT! You were randomly selected. Hurry, offer ends tonight!",
    "Earn cash by taking surveys! Make $500/day from your couch. Sign up free!",
    "Special discount for you only! 90% off luxury watches. Limited stock available.",
    "Hot singles in your area want to meet you tonight. Click here to see photos.",
    "Your PayPal account has been suspended. Verify your identity to restore access.",
    "Congratulations winner! You have won an all-expenses-paid vacation to Bahamas!",
    "FINAL NOTICE: Your subscription has expired. Renew now to avoid account deletion.",
    "Double your Bitcoin investment in 24 hours! Guaranteed returns, no risk involved.",
    "FREE adult content! Join now and get unlimited access to exclusive material.",
    "You owe back taxes. Call the IRS immediately or face arrest. This is urgent.",
    "Buy 1 get 5 free! The best online pharmacy. No prescription, discreet shipping.",
    "Make $10,000 per month promoting our products. No skills required. Start today!",
    "Your email was selected for a special reward. Claim your $500 gift card now!",
    "LAST CHANCE: Complete this survey and win a MacBook Pro. Only 3 spots left!",
    "Miracle weight loss discovered. Celebrities use this secret. Order now!",
    "Your account will be closed unless you update your information immediately!",
    "Millions waiting for you! Just pay a small processing fee to receive your funds.",
    "Online casino bonus! Get $1000 free credits today. No deposit required!",
    "Business opportunity! Earn passive income with our automated trading system.",
    "ALERT: Suspicious login detected. Verify your Gmail account or lose access forever.",
    "Get a university degree in 2 weeks! Accredited diplomas, no study required.",
    "You've been chosen to test our new product for free. Just pay shipping costs.",
    "Stop being broke! Join our MLM network and achieve financial freedom today.",
    "Celebrity-endorsed diet supplement! Lose weight without diet or exercise!",
    "Your computer is sending error reports. Download this fix tool immediately!",
    "VIP invitation! You have exclusive access to our secret trading signals.",
]

ham_samples = [
    "Hi John, just wanted to check if you are available for the team meeting tomorrow at 10 AM.",
    "Please find attached the report for Q3. Let me know if you need any clarifications.",
    "Happy birthday! Hope you have a wonderful day filled with joy and happiness.",
    "The project deadline has been moved to Friday. Please update your schedules accordingly.",
    "Can you send me the contact details of the vendor we worked with last month?",
    "Thanks for your email. I will get back to you by end of day with the requested information.",
    "Reminder: Your dentist appointment is scheduled for Wednesday at 3:30 PM.",
    "The conference room has been booked for Monday from 2 PM to 4 PM for your presentation.",
    "I wanted to share this interesting article I read about machine learning advancements.",
    "Could you please review the attached document and provide your feedback by Thursday?",
    "The annual company picnic is scheduled for next Saturday. Please RSVP by Wednesday.",
    "Just a reminder that the library book you borrowed is due back next Tuesday.",
    "Following up on our conversation from last week regarding the project proposal.",
    "The new office address is 123 Main Street, Suite 400. Parking is available on-site.",
    "I have attached my resume for the software developer position you posted last week.",
    "Thank you for attending the workshop. Your feedback helps us improve future events.",
    "The server maintenance will take place this Sunday from 2 AM to 6 AM. Plan accordingly.",
    "Please welcome our new team member, Sarah, who joins us as a data analyst from Monday.",
    "I am running 10 minutes late for our meeting. Please start without me if needed.",
    "The monthly newsletter is now available. Check out the highlights from this month.",
    "Your order #45678 has been shipped and will arrive within 3-5 business days.",
    "Just checking in to see how the project is progressing. Let me know if you need help.",
    "We are pleased to inform you that your application has been shortlisted for an interview.",
    "The Python tutorial you requested has been uploaded to the shared drive. Check it out.",
    "Lunch plans today? A few of us are going to the Italian place around the corner.",
    "I have reviewed your code and left some comments. Overall, great work on the algorithm!",
    "The quarterly budget meeting is on Thursday. Please bring your department reports.",
    "Could you help me understand the new deployment process? I am a bit confused about step 3.",
    "The wireless password for the guest network is GuestAccess2024. Valid until month end.",
    "Great job on the presentation yesterday! The client was very impressed with your work.",
    "I will be out of office from December 20 to January 3. For urgent matters, contact Lisa.",
    "The software update is ready for testing. Please check it in the staging environment.",
    "Can we reschedule our call to Thursday? I have a conflict on Wednesday afternoon.",
    "Your pull request has been approved and merged into the main branch successfully.",
    "The training session on data privacy compliance is mandatory for all staff this month.",
    "Attached is the invoice for the services rendered in November. Payment due in 30 days.",
    "We have updated our privacy policy. Please review the changes at your convenience.",
    "The book club meets every second Thursday. This month we are reading The Alchemist.",
    "Congratulations on your promotion! You truly deserve it after all your hard work.",
    "The IT helpdesk ticket you submitted has been resolved. Let us know if issue persists.",
]

# Expand dataset with variations
def create_dataset():
    rows = []
    for text in spam_samples:
        rows.append({'label': 'spam', 'text': text})
    for text in ham_samples:
        rows.append({'label': 'ham', 'text': text})

    # Duplicate with slight variation to create larger dataset
    extra = []
    for row in rows:
        extra.append(row)
        if row['label'] == 'spam':
            extra.append({'label': 'spam', 'text': row['text'].lower()})
        else:
            extra.append({'label': 'ham', 'text': row['text'] + ' Best regards.'})

    all_rows = rows + extra
    random.shuffle(all_rows)
    return all_rows

dataset = create_dataset()

with open('/home/claude/spam_detector/data/emails.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['label', 'text'])
    writer.writeheader()
    writer.writerows(dataset)

print(f"Dataset created: {len(dataset)} samples")
spam_count = sum(1 for r in dataset if r['label'] == 'spam')
ham_count = sum(1 for r in dataset if r['label'] == 'ham')
print(f"Spam: {spam_count}, Ham: {ham_count}")
