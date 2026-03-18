# bot/handlers/model_handler.py
"""Обработчики для команды /chm (Change Model)."""
import logging
from telebot import TeleBot, types as tb_types
# Импортируем данные о моделях и функции для работы с ними
from mod_llm import MODELS, DEFAULT_MODEL, get_model_info
# Импортируем функции для работы с моделью из context_service
from services.context_service import get_chat_model, set_chat_model

logger = logging.getLogger(__name__)

def register_model_handlers(bot: TeleBot):
    """Регистрация обработчиков смены модели."""

    @bot.message_handler(commands=['chm'])
    def change_model(message):
        """Смена модели нейросети."""
        chat_id = message.chat.id
        current_model_id = get_chat_model(chat_id) # Получаем текущую модель для чата
        
        markup = tb_types.InlineKeyboardMarkup(row_width=1)
        
        # Создаем кнопки для всех моделей, группируя их по семейству для удобства
        # Сначала соберем модели по семействам
        families = {}
        for model in MODELS:
            family = model.get('family', 'unknown')
            if family not in families:
                families[family] = []
            families[family].append(model)
        
        # Добавляем кнопки, сначала по семействам
        for family_name, family_models in families.items():
            # Добавляем заголовок семейства (необязательно, но удобно)
            # markup.add(tb_types.InlineKeyboardButton(text=f"-- {family_name.upper()} --", callback_data="noop"))
            
            for model in family_models:
                # Форматируем текст кнопки
                btn_text = f"{model['name']}"
                if model['id'] == current_model_id:
                    btn_text = "✅ " + btn_text
                btn = tb_types.InlineKeyboardButton(
                    text=btn_text,
                    callback_data=f"model_{model['id']}"
                )
                markup.add(btn)
        
        # Добавляем кнопку с информацией
        markup.add(tb_types.InlineKeyboardButton(
            text="ℹ️ Показать информацию о моделях",
            callback_data="model_info"
        ))
        
        # Отправляем сообщение с кнопками
        try:
            bot.send_message(
                chat_id,
                "🤖 <b>Выберите модель нейросети:</b>\n"
                "Текущая модель отмечена значком ✅",
                parse_mode='HTML',
                reply_to_message_id=message.id,
                reply_markup=markup
            )
        except Exception as e:
            logger.error(f"Ошибка отправки меню выбора модели в чате {chat_id}: {e}")
            bot.reply_to(message, "❌ Ошибка при создании меню выбора модели.")

    @bot.callback_query_handler(func=lambda call: call.data.startswith('model_') and call.data != 'model_info')
    def model_selected(call):
        """Обработка выбора модели."""
        chat_id = call.message.chat.id
        # Извлекаем ID модели из callback_data
        model_id = call.data.split('_', 1)[1] 
        
        # Находим информацию о выбранной модели
        selected_model_info = get_model_info(model_id)
        
        if selected_model_info:
            try:
                # Устанавливаем новую модель для этого чата
                set_chat_model(chat_id, model_id)
                
                # Формируем ответ (ОБНОВЛЕНО для нового формата)
                response = (
                    f"🔄 <b>Модель успешно изменена:</b>\n"
                    f"• Имя: <b>{selected_model_info['name']}</b>\n"
                    f"• Семейство: <b>{selected_model_info.get('family', 'N/A')}</b>\n"
                    # f"• Токены: <b>{selected_model_info['tokens']:,}</b>\n" # <-- УБРАНО
                    f"• Free Requests/Day: <b>{selected_model_info.get('FreeRPD', 'N/A')}</b>\n" # <-- ДОБАВЛЕНО
                    f"• Описание: {selected_model_info['description']}"
                )
                
                # Удаляем сообщение с кнопками, чтобы интерфейс был чище
                try:
                    bot.delete_message(chat_id, call.message.message_id)
                except Exception as e:
                    logger.debug(f"Не удалось удалить сообщение с кнопками в чате {chat_id}: {e}")
                    # Если не удалось удалить, просто продолжаем
                
                # Отправляем подтверждение о смене модели
                bot.send_message(
                    chat_id,
                    response,
                    parse_mode='HTML'
                )
                logger.info(f"Модель для чата {chat_id} изменена на '{model_id}' ({selected_model_info['name']}).")
                
            except Exception as e:
                error_msg = (
                    f"❌ Ошибка при установке модели:\n"
                    f"<code>{str(e)}</code>\n"
                    f"Попробуйте выбрать другую модель."
                )
                logger.error(f"Ошибка установки модели '{model_id}' для чата {chat_id}: {e}")
                bot.send_message(chat_id, error_msg, parse_mode='HTML')
        else:
            error_text = "❌ Ошибка: модель не найдена."
            logger.warning(f"Попытка выбора несуществующей модели '{model_id}' в чате {chat_id}.")
            bot.answer_callback_query(call.id, error_text) # Ответ на callback, чтобы кнопка не "зависла"
            # Также можно отправить сообщение в чат
            bot.send_message(chat_id, error_text)

    @bot.callback_query_handler(func=lambda call: call.data == "model_info")
    def show_models_info(call):
        """Показ информации о всех доступных моделях."""
        chat_id = call.message.chat.id
        response = "📊 <b>Информация о моделях:</b>\n"
        
        # Группируем модели по семействам для лучшей читаемости
        families = {}
        for model in MODELS:
            family = model.get('family', 'unknown')
            if family not in families:
                families[family] = []
            families[family].append(model)
        
        for family_name, family_models in families.items():
            response += f"\n🔸 <b>Семейство {family_name.upper()}:</b>\n"
            for model in family_models:
                response += (
                    f"• <b>{model['name']}</b>\n"
                    f"  ID: <code>{model['id']}</code>\n"
                    # f"  Токены: {model['tokens']:,}\n" # <-- УБРАНО
                    f"  Free RPD: {model.get('FreeRPD', 'N/A')}\n" # <-- ДОБАВЛЕНО
                    # f"  Стоимость ввода: ${model['price_in']}/1M токенов\n" # <-- УБРАНО
                    # f"  Стоимость вывода: ${model['price_out']}/1M токенов\n" # <-- УБРАНО
                    f"  Аудио: {'✅' if model.get('audio_support', False) else '❌'}\n"
                    f"  Описание: {model['description']}\n\n"
                )
        
        # Обрезаем, если сообщение слишком длинное (хотя Telegram позволяет длинные сообщения при правильной отправке)
        # max_length = 4096 # Максимальная длина сообщения в Telegram
        # if len(response) > max_length:
        #     response = response[:max_length-300] + "\n\n... (список обрезан) ...\n\n" + "[[Полный список доступен по запросу]]"
        
        try:
            # Редактируем существующее сообщение с кнопками
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=response,
                parse_mode='HTML'
            )
            logger.debug(f"Информация о моделях отправлена (edit) в чат {chat_id}.")
        except Exception as e1:
            logger.debug(f"Не удалось отредактировать сообщение в чате {chat_id}: {e1}. Пробуем отправить новое.")
            try:
                # Если не получилось отредактировать, отправляем новое сообщение
                # Сначала удаляем старое, если нужно
                # try:
                #     bot.delete_message(chat_id, call.message.message_id)
                # except:
                #     pass
                bot.send_message(chat_id, response, parse_mode='HTML')
                logger.debug(f"Информация о моделях отправлена (new message) в чат {chat_id}.")
            except Exception as e2:
                error_msg = f"❌ Ошибка отправки информации о моделях: {e2}"
                logger.error(error_msg)
                bot.send_message(chat_id, error_msg)
        # ❗ Важно! Отвечаем на callback query, чтобы кнопка перестала "зависать"
        bot.answer_callback_query(call.id)        
