with open(r'c:\Users\Aftab\x_gift_link_extension\controller.js', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('旧订单结果不明，请核对。', 'Previous attempt pending. Click unlock below.')
text = text.replace('创建结果不明，请核对原订单。', 'Previous attempt pending. Click unlock below.')
text = text.replace('请稍候 15 秒再创建。', 'Please wait 15 seconds before creating.')

with open(r'c:\Users\Aftab\x_gift_link_extension\controller.js', 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated controller.js successfully")
