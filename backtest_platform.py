import numpy as np
from scipy import stats
import pandas as pd
import matplotlib.pyplot as plt
from factor_generator import get_factor_table


class Platform:
    def __init__(self, monthly_return_file, quarterly_return_file, factor_name=None):

        self.monthly_return = pd.read_csv(monthly_return_file, index_col=0)
        self.quarterly_return = pd.read_csv(quarterly_return_file, index_col=0)
        self.grouped_return = None
        if factor_name:
            self.factor = get_factor_table(factor_name)

    def processor(self):

        self.monthly_return = self.monthly_return.fillna(0)
        self.quarterly_return = self.quarterly_return.fillna(0)
        self.factor = self.factor.fillna(0)

    def group(self, N, ascending=True):

        self.grouped_return = pd.DataFrame(columns=range(N))
        for date, factors in self.factor.iterrows():
            rank_factor = factors.argsort()/factors.argsort().sum() # transfer to 0-1
            ticker_list = list(rank_factor.sort_values(ascending=ascending).index)
            members = int(len(ticker_list) / N)
            gr_row = []
            for i in range(N):
                if i == N - 1:
                    grouped_tickers = ticker_list[i * members:]
                else:
                    grouped_tickers = ticker_list[i * members:(i + 1) * members]
                weighted_return = self.quarterly_return.loc[date, grouped_tickers]@rank_factor[grouped_tickers]/rank_factor[grouped_tickers].sum()
                gr_row.append(weighted_return)
            self.grouped_return = self.grouped_return.append([gr_row], ignore_index=True)

    def summary(self, group_num, factor_name=None):

        if factor_name:
            self.factor = get_factor_table(factor_name)
        assert len(self.quarterly_return) == len(self.factor)

        self.processor()
        self.group(group_num)
        gr_arr = np.array(self.grouped_return).T
        SP500 = np.array(self.quarterly_return.iloc[:, -1])

        # Student's t-test of mean return differential
        print("Student's t-test of mean return differential:")
        T_test_res = []
        for i in range(group_num):
            for j in range(i + 1, group_num):
                tmp_r = stats.ttest_ind(gr_arr[i], gr_arr[j], equal_var=stats.levene(gr_arr[i], gr_arr[j]).pvalue > 0.1)
                print(tmp_r)
                T_test_res.append(tmp_r)
        print()

        # Information Ratio
        print("Information Ratio:")
        info_ratio_res = []
        for r in gr_arr:
            ir = (r.mean() - SP500.mean()) / np.std(r - SP500)
            print(ir)
            info_ratio_res.append(ir)
        print()

        # Sharpe Ratio
        print("Sharpe Ratio:")
        Sharpe_ratio_res = []
        for r in gr_arr:
            sr = (r.mean() - 0.0318/4) / np.std(r)
            print(sr)
            Sharpe_ratio_res.append(sr)
        print()

        # Information Coefficient
        print("Information Coefficient:")
        info_coef_res = []
        for i in range(len(self.factor) - 1):
            ic = self.factor.iloc[i, :].corr(self.quarterly_return.iloc[i + 1, :])
            print(ic)
            info_coef_res.append(ic)

        fig = plt.figure(figsize=(10, 5))

        # Monotonic Test
        monotonic_graph = fig.add_subplot(1, 2, 1)
        monotonic_graph.set_title('Monotonic Test')
        # report_table = gr_arr[::]
        # print(f"ahahha {report_table}")
        count = 0
        for Q in gr_arr:
            count+=1
            # Outlier Detection and Standardization
            threshold = np.std(Q)
            Q = Q[abs(Q) < 2*threshold]
            # Q = (Q - Q.mean()) / (6 * Q.std())
            # Plot Q
            qq = (Q+1).cumprod()
            monotonic_graph.plot(qq,label=f"factor{count}")
        monotonic_graph.legend()
        # Distribution Detection
        distribution_graph = fig.add_subplot(1, 2, 2)
        distribution_graph.set_title('Distribution Detection')
        tmp = np.ravel(np.array(self.factor))
        # remove the influence from NaN
        tmp = tmp[tmp != 0]
        # remove the outlier
        tmp = tmp[abs(tmp) < 10]
        bin_width = 1
        nums = int(max(tmp) - min(tmp)) // bin_width
        plt.hist(tmp, nums)

        plt.show()
        return T_test_res, info_ratio_res, Sharpe_ratio_res, info_coef_res


bp = Platform(monthly_return_file='stock_monthly_return.csv',
              quarterly_return_file='stock_quarterly_return.csv')
bp.summary(5, "roe")


# fig = plt.figure(figsize=(10, 5))
# # Monotonic Test
# a = [[1,2,3,4,5],
#      [6,4,7,8,9],
#      [2,3,3,4,6],
#      [3,5,6,7,8],
#      [9,0,8,7,5],
#      [6,5,6,7,9],
#      [2,3,4,5,3]]
# gr_arr = np.array(a).T
# monotonic_graph = fig.add_subplot(1, 2, 1)
# monotonic_graph.set_title('Monotonic Test')
#
# for Q in gr_arr:
#     monotonic_graph.plot(Q)
#
# plt.show()
