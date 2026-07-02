def word_count(phrase):
    _count = {}
    for word in phrase.split():
        if word in _count:
            _count[word] += 1
        else:
            _count[word] = 1
    return _count
 
def print_dic(dic):
    dic =  dict(sorted(dic.items()))
    for word in dic:
        print(f"{word} - {dic[word]}")
 
if __name__ == "__main__":
    phrase = "banana apple banana mango banana mango kiwi strawberry"
    count_all = word_count(phrase)
    print_dic(count_all)
