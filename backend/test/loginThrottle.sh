for i in {1..6}; do
  curl -X POST http://127.0.0.1:8000/api/auth/login/ \
    -H "Content-Type: application/json" \
    -d '{"email":"2350152@st.uew.edu.gh","password":"wrongpassword"}'
  echo
done
