from telegram.ext import Updater, CallbackQueryHandler, CallbackContext, CommandHandler, MessageHandler, Filters
from random import choice
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
import os
import logging
from db.db import get_user, add_user, subscribe, unsubscribe, get_account, add_account, add_following, check_following, get_following, remove_following, get_shows_users, get_movies_db, store_movies, store_shows, get_shows_db
from scrapper.account import create_account, toggle_watchlist
from scrapper.functions import create_movie_caption, search_show, get_shows, get_movies, chunkalize, create_shows_caption, create_media_group_shows, create_media_group_movies
import datetime


# Required Variables
greeetings = ["hello", "hi", "howdy", "sup", "aloha"]

# Custom Keyboards

home_layout = ReplyKeyboardMarkup([
    [
        KeyboardButton("📽 Movies Updates"),
        KeyboardButton("🎬 TV-Shows Updates")
    ],
    [
        KeyboardButton("ℹ️ Help")
    ]
],
    resize_keyboard=True,
)

series_layout = ReplyKeyboardMarkup(
    resize_keyboard=True,
    one_time_keyboard=True,
    keyboard=[
        [
            KeyboardButton("Custom List Of Shows"),
            KeyboardButton("Hotest TV-Shows Daily")
        ],
        [KeyboardButton("🚫 Cancel")]
    ]
)


# Inline keys
series_layout_inline = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(
                "🎬 Today's Episodes",
                callback_data="show_today_update"
            ),

            InlineKeyboardButton(
                "🚫 Cancel Subscription",
                callback_data="show_cancle_layout"
            )
        ]
    ]
)

custom_series_layout_inline = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(
                "🎬 Today's Episodes",
                callback_data="show_today_update"
            ),

            InlineKeyboardButton(
                "🚫 Cancel Subscription",
                callback_data="show_cancle_layout"
            )
        ],
        [
            InlineKeyboardButton(
                "ℹ️ Details",
                callback_data="show_sub_details"
            )
        ]
    ]
)

cancle_sub_confirm = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("✅ Yes", callback_data="cancle_subcription"),
            InlineKeyboardButton("❌ No", callback_data="no_cancle_subcription")
        ],
    ]
)

movies_layout_inline = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(
                "📽 Missed Last List",
                callback_data="show_last_movies"
            )
        ]
    ]
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

PORT = int(os.environ.get('PORT', 5000))


# Bot Response Functions
def start(update: Update, context: CallbackContext):
    user_id = update.effective_chat.id
    first_name = update.effective_chat.first_name
    if not get_user(user_id):
        add_user(first_name, user_id)
        context.bot.send_message(
            chat_id=user_id, parse_mode="Markdown",
            text=f"*{choice(greeetings).capitalize()} {first_name}* Welcome to Screen Time 🍿",
            reply_markup=home_layout
        )
    else:
        context.bot.send_message(
            chat_id=user_id, parse_mode="Markdown",
            text=f"*{choice(greeetings).capitalize()} {first_name}* Welcome back to Screen Time 🍿",
            reply_markup=home_layout
        )


def help(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="This bot Sends Daily Or Weekly Updates On The Latest Movies And Shows.\n\nHere are some commands to help.\n\n/start - Start or Restart the bot\n/help - Get Info and Help\n/search <name of tv-show> - Search for tv-shows to follow"
    )


def echo(update: Update, context: CallbackContext):
    user_id = update.effective_chat.id
    first_name = update.effective_chat.first_name
    user = get_user(user_id)

    if update.message.text == "📽 Movies Updates":
        context.bot.send_message(
            chat_id=user_id,
            text="Movie Updates are sent to our group weekly (Sartudays 10am W.A.T)",
            reply_markup=movies_layout_inline
        )

    elif update.message.text == "🎬 TV-Shows Updates":
        if user['series_sub']:
            context.bot.send_message(
                chat_id=user_id,
                parse_mode="Markdown",
                text=f"You currently have the *{'Custom List Shows' if (user['custom']) else 'Hotest TV-Shows Daily'}* subcription.",
                reply_markup=custom_series_layout_inline if(user['custom']) else series_layout_inline)
        else:
            context.bot.send_message(
                chat_id=user_id,
                text="Alright Please Select A Subscription Type.",
                reply_markup=series_layout
            )

    elif update.message.text == "Hotest TV-Shows Daily":
        subscribe(user_id, 0)
        context.bot.send_message(
            chat_id=user_id,
            text="✅ Done. You will now get daily updates on the latest and hotest episodes",
            reply_markup=home_layout
        )

    elif update.message.text == "Custom List Of Shows":
        context.bot.send_message(
            chat_id=user_id,
            text="⌛ Hold on we are setting up your custom account...",
            reply_markup=ReplyKeyboardRemove()
        )
        if not user['custom_username'] and not user['custom_password']:
            if not get_account(user_id):
                account_id, k_value = create_account(user_id)
                if not account_id or not k_value:
                    context.bot.send_message(
                        chat_id=user_id,
                        text="😔 Something went wrong setting up your account. Please restart(/start) the bot and try again",
                        reply_markup=ReplyKeyboardRemove()
                    )
                else:
                    add_account(user_id, account_id, k_value)
                    subscribe(
                        user_id,
                        1,
                        f'screen_{user_id}',
                        f'screen_{user_id}',
                        account_id,
                        k_value
                    )
                    context.bot.send_message(
                        chat_id=user_id,
                        text="✅ Done. Use '/search <name of tv-show>' to search shows to follow.",
                        reply_markup=home_layout
                    )

            else:
                account = get_account(user_id)
                subscribe(
                    user_id,
                    1,
                    account['username'],
                    account['password'],
                    account['account_id'],
                    account['k_value'],
                )
                context.bot.send_message(
                    chat_id=user_id,
                    text="🤔 Seems like you've once had a Custom List Of Shows subscription. We will be using that.\n\nRemember you can use /search <name of tv-show> to search shows to follow",
                    reply_markup=home_layout
                )

        else:
            subscribe(
                user_id,
                1,
                user['custom_username'],
                user['custom_password'],
                user['account_id'],
                user['k_value']
            )
            context.bot.send_message(
                chat_id=user_id,
                text="🤔 Seems like you've once had a Custom List Of Shows subscription. We will be using that.\n\nRemember you can use /search <name of tv-show> to search shows to follow",
                reply_markup=home_layout
            )

    elif update.message.text == "🚫 Cancel":
        context.bot.send_message(
            chat_id=user_id,
            text="🍿 Main Menu",
            reply_markup=home_layout
        )

    elif update.message.text == "ℹ️ Help":
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="This bot Sends Daily Or Weekly Updates On The Latest Movies And Shows.\n\nHere are some commands to help.\n\n/start - Start or Restart the bot\n/help - Get Info and Help\n/search <name of tv-show> - Search for tv-shows to follow"
        )

    elif any(substring in update.message.text.lower() for substring in greeetings):
        context.bot.send_message(
            chat_id=user_id, parse_mode="Markdown",
            text=f"*{choice(greeetings).capitalize()} {first_name}*",
            reply_markup=home_layout
        )

    else:
        context.bot.send_message(
            chat_id=user_id,
            text="Hmm... 🤔 I don\'t quite understand what you mean.",
        )


def inline_button(update: Update, context: CallbackContext):
    user_id = update.effective_chat.id
    user = get_user(user_id)
    query = update.callback_query

    if query.data == "added":
        query.answer()

    elif query.data == "error":
        query.answer()

    elif query.data == "cancle_subcription":
        query.answer()
        unsubscribe(user_id)
        query.edit_message_text(text="✅ Subscription canceled successfully.")

    elif query.data == "no_cancle_subcription":
        query.answer()
        query.edit_message_text(
            "🍿 Main Menu",
        )

    elif query.data == "show_cancle_layout":
        query.answer()
        query.edit_message_text(
            f"Do you really want to cancle your *{'Custom List Of Shows' if (user['custom']) else 'Hotest TV-Shows Daily'}* subscription?",
            parse_mode="Markdown",
            reply_markup=cancle_sub_confirm
        )

    elif query.data == "show_sub_details":
        query.answer()
        query.edit_message_text("⌛ Getting subscription details...")
        shows = get_following(user_id)
        if not shows:
            query.edit_message_text(
                "*Subscription Details*\nSubscription Type: Custom List Of TV-Shows\nNumber Of Shows: None", parse_mode="Markdown"
            )
            return
        # new line and "" not allowed
        newline = "\n"
        show_name = "show_name"

        # need chucks for buttons (returns chucks of 3 items)
        chunks = [shows[x:x+3] for x in range(0, len(shows), 3)]
        chunks.append([{'show_id': 'details_view', 'show_name': 0}])

        query.edit_message_text(
            # Very dumb list comprehension but it work lol
            f"*Subscription Details*\nSubscription Type: Custom List Of TV-Shows\nNumber Of Shows: {len(shows)}\n\n*Names Of Shows*\n{newline.join([f'{num+1}. {show[show_name]}'for num,show in enumerate(shows)])}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                # creates a new row every 3 buttons
                [
                    [
                        InlineKeyboardButton(
                            # ugly but it works
                            text=f"{f'🚫 {(num + 1) + (counter*3)}' if (show['show_name'] != 0) else '✅ Done'}",
                            callback_data=f"remove_{show['show_id']}" if (show['show_name'] != 0) else "done_with_details")
                        for num, show in enumerate(chunk)
                    ]
                    for counter, chunk in enumerate(chunks)
                ]
            )
        )

    elif query.data == "show_today_update":
        query.answer()
        query.edit_message_text("⌛ Getting today's updates...")
        if user['custom']:
            try:
                if user['following']:
                    results = get_shows(user['custom_username'],
                                        user['custom_password'])
                else:
                    query.edit_message_text(
                        "🤷‍♂️ You are currently not following any TV-Show(/search to add)")
                    return
            except KeyError:
                query.edit_message_text(
                    "🤷‍♂️ You are currently not following any TV-Sho(/search to add)")
                return
        else:
            results = get_shows_db()
        if not results:
            query.edit_message_text(
                "😞 There are no TV-Shows updates for you today.")
            return
        chunks = chunkalize(results)
        for chunk in chunks:
            caption = create_shows_caption(chunk)
            media_group = create_media_group_shows(chunk, caption)
            context.bot.send_media_group(
                chat_id=user_id,
                media=media_group
            )

    elif query.data == "show_last_movies":
        query.answer()
        query.edit_message_text("⌛ Getting last movies update...")
        results = get_movies_db()
        if not results:
            query.edit_message_text("😞 There are no Movie updates to show.")
            return
        chunks = chunkalize(results)
        for chunk in chunks:
            caption = create_movie_caption(chunk)
            media_group = create_media_group_movies(chunk, caption)
            context.bot.send_media_group(
                chat_id=user_id,
                media=media_group
            )

    elif query.data == "done_with_details":
        query.answer()
        query.edit_message_text("🍿 Main Menu")


def query_show(update: Update, context: CallbackContext):
    user_id = update.effective_chat.id
    show = " ".join(context.args)
    if not show:
        context.bot.send_message(
            chat_id=user_id,
            text="🤔 You didn't pass in a valid TV-Show (search <name of tv-show>)",
            reply_markup=home_layout
        )
        return
    msg = update.message.reply_text(
        text="⌛ Hold on we are fetching results...",
    )
    results = search_show(show)
    if not results:
        msg.edit_text(
            text=f"No Shows found for the name *{show.capitalize()}*",
            parse_mode="Markdown",
        )
    else:
        msg.edit_text(
            text=f"Here are the top {len(results)} results for *{show.capitalize()}*",
            parse_mode="Markdown",
        )
        for result in reversed(results):
            context.bot.send_photo(
                chat_id=user_id,
                photo=result['image'],
                caption=f"*{result['name']}*\n\n{result['summary']}\n\n[👀 Read More]({result['link']})",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "➕ Add To Custom List", callback_data=f"add_{result['show_id']}"
                            )
                        ]
                    ]
                )
            )


def add_show(update: Update, context: CallbackContext):
    user_id = update.effective_chat.id
    user = get_user(user_id)
    query = update.callback_query
    if not user['custom']:
        context.bot.send_message(
            chat_id=user_id,
            text="Nahhh You need an active *Custom List Of Shows* subscription to do that.",
            parse_mode="Markdown"
        )
    else:
        try:
            show_id = query.data.split("_")[1]
            show_name = query.message['caption'].split("\n\n")[0]
        except:
            query.answer()
            query.edit_message_reply_markup(
                InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "❌ Error", callback_data="error"
                            )
                        ]
                    ]
                )
            )
            return

        if not check_following(user_id, show_id):
            toggle_watchlist(user, show_id)
            add_following(user_id, show_id, show_name)
            query.answer()
            query.edit_message_reply_markup(
                InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "✅ Successful", callback_data="added"
                            )
                        ]
                    ]
                )
            )
        else:
            query.answer()
            query.edit_message_reply_markup(
                InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "✅ Already Following", callback_data="added"
                            )
                        ]
                    ]
                )
            )


def remove_show(update: Update, context: CallbackContext):
    user_id = update.effective_chat.id
    query = update.callback_query
    user = get_user(user_id)
    try:
        show_id = query.data.split("_")[1]

    except:
        query.answer()
        query.edit_message_reply_markup(
            InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "❌ Error", callback_data="error"
                        )
                    ]
                ]
            )
        )
        return

    if check_following(user_id, show_id):
        # same function to add and remove TODO change function name
        toggle_watchlist(user, show_id)
        remove_following(user_id, show_id)
        # show same menu with updated list
        shows = get_following(user_id)
        if not shows:
            query.edit_message_text(
                "*Subscription Details*\nSubscription Type: Custom List Of TV-Shows\nNumber Of Shows: None", parse_mode="Markdown"
            )
            return
        newline = "\n"
        show_name = "show_name"
        chunks = [shows[x:x+3] for x in range(0, len(shows), 3)]
        chunks.append([{'show_id': 'details_view', 'show_name': 0}])
        query.edit_message_text(
            f"*Subscription Details*\nSubscription Type: Custom List Of TV-Shows\nNumber Of Shows: {len(shows)}\n\n*Names Of Shows*\n{newline.join([f'{num+1}. {show[show_name]}'for num,show in enumerate(shows)])}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text=f"{f'🚫 {(num + 1) + (counter*3)}' if (show['show_name'] != 0) else '✅ Done'}",
                            callback_data=f"remove_{show['show_id']}" if (show['show_name'] != 0) else "done_with_details")
                        for num, show in enumerate(chunk)
                    ]
                    for counter, chunk in enumerate(chunks)
                ]
            )
        )

    else:
        # else means the message is out dated so just update it.
        shows = get_following(user_id)
        if not shows:
            query.edit_message_text(
                "*Subscription Details*\nSubscription Type: Custom List Of TV-Shows\nNumber Of Shows: None", parse_mode="Markdown"
            )
            return
        newline = "\n"
        show_name = "show_name"
        chunks = [shows[x:x+3] for x in range(0, len(shows), 3)]
        chunks.append([{'show_id': 'details_view', 'show_name': 0}])
        query.edit_message_text(
            f"*Subscription Details*\nSubscription Type: Custom List Of TV-Shows\nNumber Of Shows: {len(shows)}\n\n*Names Of Shows*\n{newline.join([f'{num+1}. {show[show_name]}'for num,show in enumerate(shows)])}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text=f"{f'🚫 {(num + 1) + (counter*3)}' if (show['show_name'] != 0) else '✅ Done'}",
                            callback_data=f"remove_{show['show_id']}" if (show['show_name'] != 0) else "done_with_details")
                        for num, show in enumerate(chunk)
                    ]
                    for counter, chunk in enumerate(chunks)
                ]
            )
        )


def test(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=os.getenv(
        'group_name'), text="Up and Running!")


# Bot Job Functions
def movies_job_handler(context):
    results = get_movies()
    if not results:
        return
    store_movies(results)
    print("Movies Updated")
    chunks = chunkalize(results)
    for chunk in chunks:
        caption = create_movie_caption(chunk)
        media_group = create_media_group_movies(chunk, caption)
        context.bot.send_media_group(
            chat_id=os.getenv('group_name'),
            media=media_group
        )


def shows_job_handler(context):
    users = get_shows_users()
    for user in users:
        user_id = user['user_id']
        first_name = user['name']
        if user['custom']:
            try:
                if user['following']:
                    results = get_shows(user['custom_username'],
                                        user['custom_password'])
                else:
                    continue
            except KeyError:
                continue
        else:
            results = get_shows()
            if results:
                store_shows(results)
                print("TV-Show Updated")
        if results:
            context.bot.send_message(
                chat_id=user_id,
                text=f"*{choice(greeetings).capitalize()} {first_name}* You have *{len(results)}* TV-Show updates",
                parse_mode="Markdown"
            )
            chunks = chunkalize(results)
            for chunk in chunks:
                caption = create_shows_caption(chunk)
                media_group = create_media_group_shows(chunk, caption)
                context.bot.send_media_group(
                    chat_id=user_id,
                    media=media_group
                )


def main():

    updater = Updater(token=os.getenv('token'))

    dispatcher = updater.dispatcher

    job_queue = updater.job_queue

    # Handlers
    start_handler = CommandHandler('start', start)
    help_handler = CommandHandler('help', help)
    echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
    inline_button_handler = CallbackQueryHandler(inline_button)
    add_show_handler = CallbackQueryHandler(add_show, pattern=r"add_(\d*)")
    remove_show_handler = CallbackQueryHandler(
        remove_show, pattern=r"remove_(\d*)")
    query_show_handler = CommandHandler('search', query_show)
    test_handler = CommandHandler('test', test)
    # Dispatchers
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(echo_handler)
    dispatcher.add_handler(test_handler)
    # Make sure add_show_handler comes first
    dispatcher.add_handler(add_show_handler)
    dispatcher.add_handler(remove_show_handler)
    dispatcher.add_handler(inline_button_handler)
    dispatcher.add_handler(query_show_handler)

    # Jobs UTC Time 1hr late
    job_queue.run_daily(shows_job_handler, datetime.time(9, 20, 0))

    job_queue.run_daily(movies_job_handler, datetime.time(9, 0, 0), (5,))

    # Strat Polling
    updater.start_webhook(listen="0.0.0.0",
                          port=PORT,
                          url_path=os.getenv('token'),
                          webhook_url="https://screen-time-bot.herokuapp.com/" + os.getenv('token'))

    updater.idle()


if __name__ == '__main__':
    main()
