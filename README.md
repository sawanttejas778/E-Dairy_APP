# E-Dairy App

The **E-Dairy App** is a simple dairy management application built using Flask, Python, HTML, CSS, and MySQL. This app helps manage daily milk collection records by providing features like adding, viewing, updating customer data, calculating milk rates, and generating total amounts from CSV files.

---

## Features

- Add, view, and update milk collection records.
- Import milk data from CSV files.
- Calculate and display total milk amounts and rates.
- Offline functionality using a local database.

---

## Technologies Used

- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS
- **Database**: MySQL
- **Deployment**: Local server using Flask

---

## Project Structure

- `main.py`: Backend logic to run the app.
- `templates/index.html`: User interface layout.
- `static/style.css`: Styling for the app.
- `schema.sql`: Database schema.
- `dairy.db`: Local database storage.

---

## Prerequisites

1. **Git**: Download from [Git SCM](https://git-scm.com/downloads).
2. **Python**: Install Python 3.x from [python.org](https://www.python.org/downloads/).
3. **MySQL**: Set up MySQL or use an existing installation.

---

## Installation Instructions

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/sawanttejas778/E-Dairy_APP.git
   ```

2. **Navigate to the Project Directory**:
   ```bash
   cd E-Dairy_APP
   ```

3. **(Optional) Create a Virtual Environment**:
   ```bash
   python -m venv env
   source env/bin/activate  # For macOS/Linux
   env\Scripts\activate     # For Windows
   ```

4. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## Running the App

1. **Start the Flask App**:
   ```bash
   python main.py
   ```

2. **Open in Browser**:
   - Navigate to `http://localhost:5000` to access the app.

---

## Usage

- **Add Customer Data**: Input customer names and milk collection details.
- **Import CSV**: Upload CSV files for milk rate and total amount calculation.
- **View Records**: View all added records on the interface.

---

## Contributing

Contributions are welcome! Feel free to fork this repository, make improvements, and submit a pull request.

---

## License

This project is licensed under the MIT License.

---

## Contact

For any issues or improvements, reach out to **Tejas Atmaram Sawant** at [sawanttejas778@gmail.com](mailto:sawanttejas778@gmail.com).

