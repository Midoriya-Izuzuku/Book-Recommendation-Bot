from typing import Final
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import requests

TOKEN: Final = '6212214634:AAFGGXXr0kvnkJywVY5SU7bTGoTxD60JzT0'
BOT_USERNAME: Final = '@Bumblebee_the_auto_bot'  # Ensure the bot username is correct
GOOGLE_BOOKS_API_KEY: Final = 'AIzaSyBXGXp5qvgfNbmzrE7tw8UKS-clEHul6go'
COVERS_API_URL: Final = 'http://books.google.com/books/content?id={book_id}&printsec=frontcover&img=1&zoom=1'  # Google Books cover URL


# List of genres
GENRES = ['fiction', 'mystery', 'romance', 'science fiction', 'fantasy', 'horror', 'biography', 'history', 'self-help']


# Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello! This bot recommends top-rated and new-selling books ')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    commands = [
        "/start - Start the bot",
        "/help - Show this help message",
        "/recommend - Get book recommendations by genre"
    ]
    help_text = "Available commands:\n\n" + "\n".join(commands)
    await update.message.reply_text(help_text)


async def recommend_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(genre.capitalize(), callback_data=f"genre_{genre}")]
        for genre in GENRES
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Please choose a genre:', reply_markup=reply_markup)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    genre = query.data.split('_')[1]
    await recommend_books(update, context, genre)


async def recommend_books(update: Update, context: ContextTypes.DEFAULT_TYPE, genre: str):
    message = await update.callback_query.message.reply_text("Fetching the right picks for you...")

    top_books = get_top_rated_books(genre)
    new_books = get_new_books(genre)

    if top_books:
        await message.delete()  # Delete the "Fetching..." message
        await update.callback_query.message.reply_text(f'Top rated {genre.capitalize()} books:')
        for book in top_books:
            await send_book_details(update, book)

    if new_books:
        await message.delete()  # Delete the "Fetching..." message
        await update.callback_query.message.reply_text(f'New {genre.capitalize()} releases:')
        for book in new_books:
            await send_book_details(update, book)

    if not top_books and not new_books:
        await message.delete()  # Delete the "Fetching..." message
        await update.callback_query.message.reply_text(f'Sorry, no books found for {genre.capitalize()}.')


async def send_book_details(update: Update, book: dict):
    title = f"<b>{book['volumeInfo'].get('title', 'Unknown Title')}</b>"
    authors = ", ".join(book['volumeInfo'].get('authors', ['Unknown Author']))
    cover_url = book['volumeInfo'].get('imageLinks', {}).get('thumbnail', 'No Cover Available')

    message = f"{title}\nAuthors: {authors}\n"
    if 'publishedDate' in book['volumeInfo']:
        message += f"First Published: {book['volumeInfo']['publishedDate']}\n"

    await update.callback_query.message.reply_photo(cover_url, caption=message, parse_mode='HTML')


def get_top_rated_books(genre: str, limit: int = 5):
    url = f'https://www.googleapis.com/books/v1/volumes?q={genre}&orderBy=relevance&maxResults={limit}&key={GOOGLE_BOOKS_API_KEY}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        books = data.get('items', [])
        return books
    return []


def get_new_books(genre: str, limit: int = 5):
    url = f'https://www.googleapis.com/books/v1/volumes?q={genre}&orderBy=newest&maxResults={limit}&key={GOOGLE_BOOKS_API_KEY}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        books = data.get('items', [])
        return books
    return []


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    if 'start' in text:
        await start_command(update, context)
    elif 'help' in text:
        await help_command(update, context)
    elif 'recommend' in text:
        await recommend_command(update, context)
    else:
        await update.message.reply_text("I don't understand that command.")


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')


if __name__ == '__main__':
    print('Starting bot...')
    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('recommend', recommend_command))

    # Callbacks
    app.add_handler(CallbackQueryHandler(button))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Errors
    app.add_error_handler(error)

    # Polling the bot
    print('Polling...')
    app.run_polling(poll_interval=3)
