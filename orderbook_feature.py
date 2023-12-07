from math import trunc
import timeit
import pandas as pd

# 교수님이 올려주신 lecture-05-feature-calc.py, lecture-05-feature-mid.py, lecture-05-feature-bookI.py를 바탕으로 일부 수정하여 코드 작성하였습니다.
# 저희가 직접 수집한 데이터를 최대한 활용하고자 했기 때문에 order book 데이터를 기반으로 한 feature만 있습니다.
# 따라서 trade 데이터를 처리하는 부분은 없습니다!

# 함수 구조도
# main
# |
# └── faster_calc_indicators : feature들을 계산
#     |
#     ├── get_sim_df : csv 파일 읽어오기
#     |
#     ├── cal_mid_price : mid_type에 따라 아래 함수 호출
#     |   ├── calculate_weighted_mid_price
#     |   └── calculate_market_mid_price
#     |
#     ├── cal_taegeon_feature : 저희가 새롭게 정의한 feature입니다. (_l_indicator_fn[indicator]에 의해 호출됨)
#     |
#     ├── cal_book_imb : book imbalance 계산 (_l_indicator_fn[indicator]에 의해 호출됨)
#     |
#     └── df_dict_to_csv : dict -> csv로 변환

# raw_fn : 수집한 Order_book 파일 이름
# fn : 추출한 feature 저장하는 파일 이름
# raw_fn 자신의 orderbook 파일 이름으로 변경하기
raw_fn = "2023-11-11-upbit-btc-orderbook.csv"
fn = "2023-11-11-upbit-btc-feature.csv"


# dict 를 csv로 변환
def df_dict_to_csv(data, file_path):
    df = pd.DataFrame.from_dict(data)
    df.to_csv(file_path, index=False)


# csv 파일 읽어오기
def get_sim_df(fn):
    print(f"loading... {fn}")
    # 여기서 파일을 읽는다.
    df = pd.read_csv(fn).apply(pd.to_numeric, errors="ignore")
    # timestamp 기준 묶기
    # 그룹은 timestamp 기준으로 묶인 데이터프레임
    group = df.groupby(["timestamp"])
    return group


# mid_price_wt 계산 함수
def calculate_weighted_mid_price(gr_bid_level, gr_ask_level, level):
    bid_price_mean = gr_bid_level.head(level)["price"].mean()
    ask_price_mean = gr_ask_level.head(level)["price"].mean()
    return (bid_price_mean + ask_price_mean) * 0.5


# mid_price_mkt 계산 함수
def calculate_market_mid_price(
    bid_top_price, ask_top_price, bid_top_level_qty, ask_top_level_qty
):
    mid_price = (
        bid_top_price * ask_top_level_qty + ask_top_price * bid_top_level_qty
    ) / (bid_top_level_qty + ask_top_level_qty)
    return trunc(mid_price)


# mid_pricec 계산 함수 : 위 wt, mkt 계산 함수를 내부에서 호출, level을 매개변수로 설정(디폴트:5)
def cal_mid_price(gr_bid_level, gr_ask_level, mid_type, level=5):
    if len(gr_bid_level) > 0 and len(gr_ask_level) > 0:
        # 필요한 기본 데이터 추출
        bid_top_price = gr_bid_level.iloc[0].price
        bid_top_level_qty = gr_bid_level.iloc[0].quantity
        ask_top_price = gr_ask_level.iloc[0].price
        ask_top_level_qty = gr_ask_level.iloc[0].quantity
        # 종류에 따라 맞는 함수 호출
        if mid_type == "wt":
            mid_price = calculate_weighted_mid_price(gr_bid_level, gr_ask_level, level)
        elif mid_type == "mkt":
            mid_price = calculate_market_mid_price(
                bid_top_price, ask_top_price, bid_top_level_qty, ask_top_level_qty
            )
        return (
            mid_price,
            bid_top_price,
            ask_top_price,
            bid_top_level_qty,
            ask_top_level_qty,
        )

    else:
        print("Error: serious cal_mid_price")
        return (-1, -1, -2, -1, -1)


# 우리만의 새로운 feature 정의 :
# 고안한 팀원의 이름을 빌렸습니다.
# 공식 : bid quantity 총합 - ask quantity 총합 , 결과 : 하나의 실수값
# bid와 ask간의 우세 정도를 나타냅니다. 양수 : bid가 우세, 음수 : ask가 우세
# 추가적인 비율 조정 없이 bid quantity와 ask quantity의 절대적인 양을 비교
# 이를 통해 시장의 압력 정도를 보다 직관적으로 확인할 수 있음
def cal_taegeon_feature(gr_bid_level, gr_ask_level):
    return sum(gr_bid_level.quantity) - sum(gr_ask_level.quantity)


# Feature: calculating 'bookI' using orderbook
# book imbalance
# @params
# gr_bid_level: all bid level
# gr_ask_level: all ask level
# diff: summary of trade, refer to get_diff_count_units()
# var: can be empty
# mid: midprice
def cal_book_imb(param, gr_bid_level, gr_ask_level, mid):
    mid_price = mid

    ratio = param[1]
    # 당장 필요하지 않아서 주석처리
    # level = param[0]
    interval = param[2]

    # 당장 필요하지 않아서 주석처리
    # _flag = var["_flag"]
    # if _flag:  # skipping first line
    #     var["_flag"] = False
    #     return 0.0

    quant_v_bid = gr_bid_level.quantity**ratio
    price_v_bid = gr_bid_level.price * quant_v_bid

    quant_v_ask = gr_ask_level.quantity**ratio
    price_v_ask = gr_ask_level.price * quant_v_ask

    # quant_v_bid = gr_r[(gr_r['type']==0)].quantity**ratio
    # price_v_bid = gr_r[(gr_r['type']==0)].price * quant_v_bid

    # quant_v_ask = gr_r[(gr_r['type']==1)].quantity**ratio
    # price_v_ask = gr_r[(gr_r['type']==1)].price * quant_v_ask

    askQty = quant_v_ask.values.sum()
    bidPx = price_v_bid.values.sum()
    bidQty = quant_v_bid.values.sum()
    askPx = price_v_ask.values.sum()
    bid_ask_spread = interval

    book_price = 0  # because of warning, divisible by 0
    if bidQty > 0 and askQty > 0:
        book_price = (((askQty * bidPx) / bidQty) + ((bidQty * askPx) / askQty)) / (
            bidQty + askQty
        )

    indicator_value = (book_price - mid_price) / bid_ask_spread
    # indicator_value = (book_price - mid_price)

    return indicator_value


# _l_indicator_fn : indicator를 구하는 함수 key : indicator 이니셜, value : 함수
# _l_indicator_name : indicator의 풀네임 key : indicator 이니셜, value : 풀네임
_l_indicator_fn = {"BI": cal_book_imb, "TG": cal_taegeon_feature}
_l_indicator_name = {"BI": "book_imbalance", "TG": "taegeon"}


# 주된 계산을 하는 함수
def calc_indicators(raw_fn):
    # 타이머 시작
    start_time = timeit.default_timer()

    # raw_fn 인자로 전달, csv 파일 읽기
    group_o = get_sim_df(raw_fn)

    # 타이머 종료
    delay = timeit.default_timer() - start_time
    print("df loading delay: %.2fs" % delay)

    # 레벨 변수 설정
    level_1 = 2
    level_2 = 5

    # (level, ratio, interval seconds, mid price type)
    # book imbalance 매개변수로 기존 매개변수에서 mid price type(mkt or wt)를 추가하였습니다.
    book_imbalance_params = [
        (level_1, 0.2, 1, "mkt"),
        (level_1, 0.2, 1, "wt"),
        (level_2, 0.2, 1, "mkt"),
        (level_2, 0.2, 1, "wt"),
        (level_1, 0.6, 1, "mkt"),
        (level_1, 0.6, 1, "wt"),
        (level_2, 0.6, 1, "mkt"),
        (level_2, 0.6, 1, "wt"),
    ]
    # 저희가 새로만든 feature : taegeon의 매개변수입니다. orderbook의 level만 받습니다.

    taegeon_params = [(level_1,), (level_2,)]
    # _dict : indicator 종류에 따른 결과 저장
    # _dict_indicators : 최종 결과 저장. key: columns value: data
    # varialbes : 당장 사용하지 않음
    # variables = {}
    _dict = {}
    _dict_indicators = {}

    # _dict에 book imbalance의 약자와 매개변수 업데이트
    for p in book_imbalance_params:
        indicator = "BI"
        _dict.update({(indicator, p): []})
        # 당장 필요하지 않아서 주석 처리
        # _dict_var = init_indicator_var(indicator, p)
        # variables.update({(indicator, p): _dict_var})

    # _dict에 taegeon의 약자와 매개변수 업데이트
    for p in taegeon_params:
        indicator = "TG"
        _dict.update({(indicator, p): []})

    _timestamp = []
    _mid_price_wt = []
    _mid_price_mkt = []
    _taegeon = []
    seq = 0

    # order book 그룹별 iterate
    # 여기서 group_o는 시간별로 묶인 데이터
    for gr_o in group_o:
        # 빈 경우 예외처리
        if gr_o is None:
            print("Warning: group is empty")
            continue
        # 현재 timestamp 저장
        timestamp = (gr_o[1].iloc[0])["timestamp"]

        # 당장 필요하지 않아서 주석 처리
        # if banded:
        #     gr_o = agg_order_book(gr_o[1], timestamp)
        #     gr_o = gr_o.reset_index()
        #     del gr_o["index"]
        # else:

        # 튜플 형식에서 데이터 부분 떼오기
        gr_o = gr_o[1]

        # bid와 ask 부분 나누기
        gr_bid_level = gr_o[gr_o.type == 0]
        gr_ask_level = gr_o[gr_o.type == 1]
        # mid_price 구하기
        mid_price = {}
        mid_price["wt"] = cal_mid_price(gr_bid_level, gr_ask_level, "wt")[0]
        mid_price["mkt"], bid, ask = cal_mid_price(gr_bid_level, gr_ask_level, "mkt")[
            :3
        ]

        # bid가 ask 보다 크면 데이터가 잘못된 것
        if bid >= ask:
            seq += 1
            continue

        # 각각의 리스트 업데이트
        _timestamp.append(timestamp)
        _mid_price_wt.append(mid_price["wt"])
        _mid_price_mkt.append(mid_price["mkt"])
        _dict_group = {}

        for indicator, p in _dict.keys():  # indicator_fn, param
            # book imbalance의 p = (level, ratio, interval seconds, mid price type)
            # taegeon의 p = (level)
            level = p[0]

            if level not in _dict_group:
                # orig_level = level
                level = min(level, len(gr_bid_level), len(gr_ask_level))

                _dict_group[level] = (
                    gr_bid_level.head(level),
                    gr_ask_level.head(level),
                )

            p1 = ()
            if len(p) == 1:
                p1 = p
                _i = _l_indicator_fn[indicator](
                    _dict_group[level][0], _dict_group[level][1]
                )
            elif len(p) == 4:
                # book imbalance의 p = (level, ratio, interval seconds, mid price type)
                p1 = (level, p[1], p[2], p[3])
                _i = _l_indicator_fn[indicator](
                    p1,
                    _dict_group[level][0],
                    _dict_group[level][1],
                    # live_cal_book_i_v1에서 var[flag]를 주석처리하며 같이 주석처리했음
                    # variables[(indicator, p)],
                    mid_price[p1[3]],
                )
            # 당장 필요하지 않아서 주석처리
            # if len(p) == 4:
            #     p1 = (p[0], level, p[2], p[3])
            # print indicator

            _dict[(indicator, p)].append(_i)
        # indicator 이름 형식 변환
        for indicator, p in _dict.keys():  # indicator_fn, param
            if indicator == "TG":
                col_name = "%s-%s" % (
                    _l_indicator_name[indicator].replace("_", "-"),
                    p[0],
                )
            else:
                col_name = "%s-%s-%s-%s-%s" % (
                    _l_indicator_name[indicator].replace("_", "-"),
                    p[0],
                    p[1],
                    p[2],
                    p[3],
                )
            # 당장 필요하지 않아서 주석처리
            # if indicator == "TIv1" or indicator == "TIv2":
            #     col_name = "%s-%s-%s-%s-%s" % (
            #         _l_indicator_name[indicator].replace("_", "-"),
            #         p[0],
            #         p[1],
            #         p[2],
            #         p[3],
            #     )

            # indicator별로 저장된 결과를 _dict_indicators에 업데이트
            _dict_indicators[col_name] = _dict[(indicator, p)]

        # 각각의 key값에 맞는 리스트를 딕셔너리에 업데이트
        _dict_indicators["timestamp"] = _timestamp
        _dict_indicators["mid_price_wt"] = _mid_price_wt
        _dict_indicators["mid_price_mkt"] = _mid_price_mkt
        # 우리만의 새로운 feature 정의
        seq += 1
        print(seq)

    # csv 파일로 변환
    df_dict_to_csv(_dict_indicators, fn)


if __name__ == "__main__":
    calc_indicators(raw_fn)
