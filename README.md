# Transaction Management System

## Working Flow

1. **Application Start**
   - Project run karne ke liye `app.py` file execute hoti hai.
   - Browser me main page open hota hai.

2. **Login Page**
   - Sabse pehle user ko login page dikhai deta hai.
   - Yaha username aur password enter karna hota hai.

3. **Authentication**
   - System entered credentials ko verify karta hai.
   - Agar credentials valid hote hain to user next page par redirect hota hai.
   - Agar invalid hote hain to error message show hota hai.

4. **User Login Flow**
   - Normal user login karne ke baad `home.html` page open hota hai.
   - User apna account details dekh sakta hai.
   - User transaction perform kar sakta hai.
   - User apni transaction history `history.html` page par dekh sakta hai.

5. **Admin Login Flow**
   - Admin login karne par `admin_home.html` page open hota hai.
   - Admin sabhi users ke transactions ko monitor kar sakta hai.
   - Admin `admin_history.html` page par complete transaction history dekh sakta hai.

6. **Additional Page**
   - `ai.html` page extra functionality ke liye use ki gayi hai.

---

## Pre-Stored User Credentials (For Testing)

### Users

| Username   | Password  |
|------------|-----------|
| Ghanshyam  | gha123    |
| Harsh      | harsh123  |

### Admin

| Username | Password    |
|----------|-------------|
| Admin    | admin@123   |
