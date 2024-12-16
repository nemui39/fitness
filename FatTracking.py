# ファイルの先頭で、他のインポートの前にこれらを追加
import matplotlib
# バックエンドを設定（'TkAgg', 'Qt5Agg', 'Agg' のいずれかを試してください）
matplotlib.use('Agg')  
import matplotlib.pyplot as plt
from matplotlib import font_manager
import pandas as pd
from datetime import datetime, timedelta
import json
import numpy as np
import sys
import os



# 日本語フォントの直接設定
font_path = '/usr/share/fonts/truetype/fonts-japanese-gothic.ttf'  # システムで検出されたパス
font_prop = font_manager.FontProperties(fname=font_path)
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['IPAGothic']
plt.rcParams['axes.unicode_minus'] = False



class SimpleFitnessTracker:
    def __init__(self, start_weight=68, start_bf=24, target_weight_loss=10, target_bf_loss=10, duration_days=168):
        self.start_weight = start_weight
        self.start_bf = start_bf
        self.target_weight_loss = target_weight_loss
        self.target_bf_loss = target_bf_loss
        self.duration_days = duration_days
        self.records = []
        # 1kg の脂肪のカロリー価（約7700kcal）
        self.cal_per_kg_fat = 7700
        self.load_data()
        self.ideal_curve = self.generate_ideal_curve()

    def load_data(self):
        """JSONファイルからデータを読み込む"""
        try:
            with open('fitness_data.json', 'r') as f:
                json_records = json.load(f)
                self.records = []
                for record in json_records:
                    # 日付文字列をdatetimeオブジェクトに変換
                    record['date'] = datetime.strptime(record['date'], '%Y-%m-%d %H:%M:%S')
                    # 古いデータ形式との互換性を保持
                    if 'weight_diff_from_ideal' not in record:
                        record['weight_diff_from_ideal'] = 0
                        record['bf_diff_from_ideal'] = 0
                    self.records.append(record)
                
                # 最初のレコードがあれば、それを初期値として使用
                if self.records:
                    self.start_weight = self.records[0]['weight']
                    self.start_bf = self.records[0]['body_fat']
                    
        except FileNotFoundError:
            print("新規データファイルを作成します。")
            self.records = []
        except json.JSONDecodeError:
            print("データファイルが破損しています。新規作成します。")
            self.records = []
        except Exception as e:
            print(f"データ読み込み中にエラーが発生しました: {str(e)}")
            self.records = []

    def save_data(self):
        """データをJSONファイルに保存"""
        try:
            with open('fitness_data.json', 'w') as f:
                json_records = []
                for record in self.records:
                    record_copy = record.copy()
                    record_copy['date'] = record_copy['date'].strftime('%Y-%m-%d %H:%M:%S')
                    json_records.append(record_copy)
                json.dump(json_records, f)
        except Exception as e:
            print(f"データ保存中にエラーが発生しました: {str(e)}")
    
    def generate_ideal_curve(self):
        """理想的な減少曲線を生成"""
        # 開始日を設定（記録がある場合は最初の記録の日付、ない場合は現在の日付）
        start_date = self.records[0]['date'] if self.records else datetime.now()
        
        # 開始日から指定日数分の日付を生成
        dates = [start_date + timedelta(days=x) for x in range(self.duration_days + 1)]
        
        # 非線形な減少曲線を生成
        days = np.array(range(self.duration_days + 1))
        weight_loss = self.target_weight_loss * (1 - np.exp(-days/120))
        bf_loss = self.target_bf_loss * (1 - np.exp(-(days-7)/100))
        
        ideal_weights = self.start_weight - weight_loss
        ideal_bf = self.start_bf - bf_loss
        
        return pd.DataFrame({
            'date': dates,
            'ideal_weight': ideal_weights,
            'ideal_bf': ideal_bf
        })
    
    def add_record(self):
        try:
            date = datetime.now()
            weight = float(input("体重(kg)を入力してください: "))
            body_fat = float(input("体脂肪率(%)を入力してください: "))
            
            # 理想値との差分を計算
            ideal_today = self.ideal_curve[self.ideal_curve['date'].dt.date == date.date()]
            if not ideal_today.empty:
                weight_diff = weight - ideal_today['ideal_weight'].iloc[0]
                bf_diff = body_fat - ideal_today['ideal_bf'].iloc[0]
            else:
                weight_diff = 0
                bf_diff = 0
            
            record = {
                'date': date,
                'weight': weight,
                'body_fat': body_fat,
                'weight_diff_from_ideal': weight_diff,
                'bf_diff_from_ideal': bf_diff
            }
            self.records.append(record)
            self.save_data()
            print("\n記録を保存しました。")
            self.show_daily_stats(record)
        except ValueError:
            print("正しい数値を入力してください。")
    
    def show_daily_stats(self, record):
        """その日の統計情報を表示"""
        print("\n=== 本日の状況 ===")
        print(f"体重: {record['weight']:.2f}kg (目標との差: {record['weight_diff_from_ideal']:+.2f}kg)")
        print(f"体脂肪率: {record['body_fat']:.2f}% (目標との差: {record['bf_diff_from_ideal']:+.2f}%)")
        
        if len(self.records) > 1:
            prev_record = self.records[-2]
            weight_change = record['weight'] - prev_record['weight']
            bf_change = record['body_fat'] - prev_record['body_fat']
            print(f"\n前回から体重: {weight_change:+.1f}kg")
            print(f"前回から体脂肪率: {bf_change:+.1f}%")
    
    def show_stats(self):
        if not self.records:
            print("記録がありません。")
            return
                
        df = pd.DataFrame(self.records)

        # 除脂肪体重と脂肪量の計算
        df['lean_body_mass'] = df['weight'] * (100 - df['body_fat']) / 100
        df['fat_mass'] = df['weight'] * df['body_fat'] / 100

        # 5日移動平均の計算
        df['weight_ma5'] = df['weight'].rolling(window=5).mean()
        df['bf_ma5'] = df['body_fat'].rolling(window=5).mean()
        df['lean_body_mass_ma5'] = df['lean_body_mass'].rolling(window=5).mean()
        df['fat_mass_ma5'] = df['fat_mass'].rolling(window=5).mean()
        
        # 5日シフトした移動平均の計算
        df['weight_ma5_shift'] = df['weight_ma5'].shift(5)
        df['bf_ma5_shift'] = df['bf_ma5'].shift(5)
        df['lean_body_mass_ma5_shift'] = df['lean_body_mass_ma5'].shift(5)
        df['fat_mass_ma5_shift'] = df['fat_mass_ma5'].shift(5)
        
        print("\n=== 移動平均の統計 ===")
        if len(df) >= 5:
            # 体重の移動平均統計
            current_weight_ma = df['weight_ma5'].iloc[-1]
            prev_weight_ma = df['weight_ma5_shift'].iloc[-1]
            
            # 体脂肪の移動平均統計
            current_bf_ma = df['bf_ma5'].iloc[-1]
            prev_bf_ma = df['bf_ma5_shift'].iloc[-1]
            
            # 除脂肪体重の移動平均統計
            current_lean_mass_ma = df['lean_body_mass_ma5'].iloc[-1]
            prev_lean_mass_ma = df['lean_body_mass_ma5_shift'].iloc[-1]
            
            # 脂肪量の移動平均統計
            current_fat_mass_ma = df['fat_mass_ma5'].iloc[-1]
            prev_fat_mass_ma = df['fat_mass_ma5_shift'].iloc[-1]
            
            if not np.isnan(prev_weight_ma):
                weight_ma_change = current_weight_ma - prev_weight_ma
                daily_cal_change = (weight_ma_change * self.cal_per_kg_fat) / 5
                
                # カロリー収支の判定
                if abs(daily_cal_change) <= 50:
                    cal_status = "メンテナンスカロリー"
                elif daily_cal_change > 50:
                    cal_status = "オーバーカロリー"
                else:
                    cal_status = "アンダーカロリー"
                
                print(f"5日前の5日平均体重: {prev_weight_ma:.2f}kg")  
                print(f"直近5日平均体重: {current_weight_ma:.2f}kg")
                print(f"5日前の5日平均との差: {weight_ma_change:+.2f}kg")
                print(f"1日あたりの推定カロリー収支: {daily_cal_change:.0f}kcal")
                print(f"カロリー収支状態: {cal_status}")
            
            if not np.isnan(prev_bf_ma):
                bf_ma_change = current_bf_ma - prev_bf_ma
                print(f"\n5日前の5日平均体脂肪率: {prev_bf_ma:.2f}%")                
                print(f"直近5日平均体脂肪率: {current_bf_ma:.2f}%")
                print(f"5日前の5日平均との差: {bf_ma_change:+.2f}%")
            
            # 除脂肪体重の統計
            if not np.isnan(prev_lean_mass_ma):
                lean_mass_ma_change = current_lean_mass_ma - prev_lean_mass_ma
                print(f"\n5日前の5日平均除脂肪体重: {prev_lean_mass_ma:.2f}kg")
                print(f"直近5日平均除脂肪体重: {current_lean_mass_ma:.2f}kg")
                print(f"5日前の5日平均との差: {lean_mass_ma_change:+.2f}kg")
            
            # 脂肪量の統計
            if not np.isnan(prev_fat_mass_ma):
                fat_mass_ma_change = current_fat_mass_ma - prev_fat_mass_ma
                print(f"\n5日前の5日平均脂肪量: {prev_fat_mass_ma:.2f}kg")
                print(f"直近5日平均脂肪量: {current_fat_mass_ma:.2f}kg")
                print(f"5日前の5日平均との差: {fat_mass_ma_change:+.2f}kg")
        
        print("\n=== 全体統計 ===")
        # 経過日数を計算
        total_days = (df['date'].iloc[-1] - df['date'].iloc[0]).days

        # 安全な日数計算
        if total_days == 0:
            total_days = 1
        
        # 体重関連の統計
        start_weight = df['weight'].iloc[0]
        current_weight = df['weight'].iloc[-1]
        weight_change = current_weight - start_weight
        
        # 体重変化率の計算
        weight_change_rate_percent = (current_weight - start_weight) / start_weight * 100
        
        # 安全な1日あたりの変化量計算
        daily_weight_change = weight_change / total_days

        print(f"経過日数: {total_days}日")
        print(f"開始時体重: {start_weight:.2f}kg")
        print(f"現在の体重: {current_weight:.2f}kg")
        print(f"体重変化率: {weight_change_rate_percent:+.2f}%")
        print(f"総変化量: {weight_change:+.2f}kg")
        print(f"1日あたりの体重変化: {daily_weight_change:+.3f}kg/日")

        # 体脂肪率関連の統計
        start_bf = df['body_fat'].iloc[0]
        current_bf = df['body_fat'].iloc[-1]
        bf_change = current_bf - start_bf
        
        # 体脂肪率変化率の計算
        bf_change_rate_percent = (current_bf - start_bf) / start_bf * 100
        
        # 安全な1日あたりの変化量計算
        daily_bf_change = bf_change / total_days

        print(f"\n開始時体脂肪率: {start_bf:.2f}%")
        print(f"現在の体脂肪率: {current_bf:.2f}%")
        print(f"体脂肪率変化率: {bf_change_rate_percent:+.2f}%")
        print(f"総変化量: {bf_change:+.2f}%")
        print(f"1日あたりの体脂肪率変化: {daily_bf_change:+.3f}%/日")
        
        # カロリー収支の計算と表示
        if len(df) >= 2:
            # 実際の体重変化から総カロリー収支を計算
            weight_change = df['weight'].iloc[-1] - df['weight'].iloc[0]
            actual_calories = weight_change * self.cal_per_kg_fat
            actual_daily_calories = actual_calories / total_days
            
            # 理想的な体重減少から目標カロリー収支を計算
            target_daily_weight_loss = self.target_weight_loss / self.duration_days
            target_daily_calories = -target_daily_weight_loss * self.cal_per_kg_fat
            
            print("\n=== カロリー収支 ===")
            print(f"目標1日カロリー収支: {target_daily_calories:.0f}kcal")
            print(f"実際の1日平均カロリー収支: {actual_daily_calories:.0f}kcal")
            print(f"目標との差異: {actual_daily_calories - target_daily_calories:+.0f}kcal/日")
            
            # 目標達成予測
            weight_change_rate = (df['weight'].iloc[-1] - df['weight'].iloc[0]) / total_days
            if weight_change_rate != 0:
                days_to_target = abs((self.start_weight - self.target_weight_loss - df['weight'].iloc[-1]) / weight_change_rate)
                print(f"\n現在のペースでの目標達成予想日数: {days_to_target:.0f}日")
            else:
                print("\n現在のペースでは目標達成予想を計算できません。")
    
    def plot_progress(self):
        if not self.records:
            print("グラフを表示するための記録がありません。")
            return
                
        try:
            # データフレームの準備
            df = pd.DataFrame(self.records)
            df['date'] = pd.to_datetime(df['date'])
            
            # 除脂肪体重と脂肪量の計算
            df['lean_body_mass'] = df['weight'] * (100 - df['body_fat']) / 100
            df['fat_mass'] = df['weight'] * df['body_fat'] / 100
            
            # 5日と14日の移動平均の計算
            df['weight_ma5'] = df['weight'].rolling(window=5).mean()
            df['weight_ma14'] = df['weight'].rolling(window=14).mean()
            df['bf_ma5'] = df['body_fat'].rolling(window=5).mean()
            df['bf_ma14'] = df['body_fat'].rolling(window=14).mean()
            df['lean_body_mass_ma5'] = df['lean_body_mass'].rolling(window=5).mean()
            df['lean_body_mass_ma14'] = df['lean_body_mass'].rolling(window=14).mean()
            df['fat_mass_ma5'] = df['fat_mass'].rolling(window=5).mean()
            df['fat_mass_ma14'] = df['fat_mass'].rolling(window=14).mean()
            
            # シグマ（標準偏差）の計算
            sigma_weight = df['weight'].std()
            sigma_bf = df['body_fat'].std()
            sigma_lean_mass = df['lean_body_mass'].std()
            sigma_fat_mass = df['fat_mass'].std()
            
            # グラフの作成
            plt.figure(figsize=(15, 12))
            
            # 体重のプロット
            plt.subplot(2, 2, 1)
            plt.fill_between(self.ideal_curve['date'], 
                            self.ideal_curve['ideal_weight'] - 2*sigma_weight,
                            self.ideal_curve['ideal_weight'] + 2*sigma_weight,
                            color='gray', alpha=0.1, label='±2σ')
            plt.fill_between(self.ideal_curve['date'], 
                            self.ideal_curve['ideal_weight'] - sigma_weight,
                            self.ideal_curve['ideal_weight'] + sigma_weight,
                            color='gray', alpha=0.2, label='±1σ')
            plt.plot(self.ideal_curve['date'], self.ideal_curve['ideal_weight'], 
                    '--', color='gray', label='理想曲線')
            plt.plot(df['date'], df['weight'], 'o-', color='blue', label='実績', alpha=0.5)
            plt.plot(df['date'], df['weight_ma5'], '-', color='red', label='5日移動平均')
            plt.plot(df['date'], df['weight_ma14'], '-', color='darkred', label='14日移動平均', linewidth=2)
            plt.title('体重推移', fontproperties=font_prop, fontsize=12)
            plt.xlabel('日付', fontproperties=font_prop, fontsize=10)
            plt.ylabel('体重 (kg)', fontproperties=font_prop, fontsize=10)
            plt.grid(True)
            plt.legend(prop=font_prop)
            
            # 体脂肪率のプロット
            plt.subplot(2, 2, 2)
            plt.fill_between(self.ideal_curve['date'], 
                            self.ideal_curve['ideal_bf'] - 2*sigma_bf,
                            self.ideal_curve['ideal_bf'] + 2*sigma_bf,
                            color='gray', alpha=0.1, label='±2σ')
            plt.fill_between(self.ideal_curve['date'], 
                            self.ideal_curve['ideal_bf'] - sigma_bf,
                            self.ideal_curve['ideal_bf'] + sigma_bf,
                            color='gray', alpha=0.2, label='±1σ')
            plt.plot(self.ideal_curve['date'], self.ideal_curve['ideal_bf'], 
                    '--', color='gray', label='理想曲線')
            plt.plot(df['date'], df['body_fat'], 'o-', color='orange', label='実績', alpha=0.5)
            plt.plot(df['date'], df['bf_ma5'], '-', color='red', label='5日移動平均')
            plt.plot(df['date'], df['bf_ma14'], '-', color='darkred', label='14日移動平均', linewidth=2)
            plt.title('体脂肪率推移', fontproperties=font_prop, fontsize=12)
            plt.xlabel('日付', fontproperties=font_prop, fontsize=10)
            plt.ylabel('体脂肪率 (%)', fontproperties=font_prop, fontsize=10)
            plt.grid(True)
            plt.legend(prop=font_prop)
            
            # 除脂肪体重と脂肪量のグラフのY軸範囲を計算
            lean_min = df['lean_body_mass'].min()
            lean_max = df['lean_body_mass'].max()
            fat_min = df['fat_mass'].min()
            fat_max = df['fat_mass'].max()

            # それぞれの変動幅を計算
            lean_range = lean_max - lean_min
            fat_range = fat_max - fat_min

            # より大きい方の変動幅を基準にする
            max_range = max(lean_range, fat_range)
            padding = max_range * 0.1

            # それぞれのデータの中心点を計算
            lean_center = (lean_max + lean_min) / 2
            fat_center = (fat_max + fat_min) / 2

            # 除脂肪体重のプロット
            plt.subplot(2, 2, 3)
            plt.plot(df['date'], df['lean_body_mass'], 'o-', color='green', label='除脂肪体重', alpha=0.5)
            plt.plot(df['date'], df['lean_body_mass_ma5'], '-', color='forestgreen', label='5日移動平均')
            plt.plot(df['date'], df['lean_body_mass_ma14'], '-', color='darkgreen', label='14日移動平均', linewidth=2)
            plt.title('除脂肪体重推移', fontproperties=font_prop, fontsize=12)
            plt.xlabel('日付', fontproperties=font_prop, fontsize=10)
            plt.ylabel('除脂肪体重 (kg)', fontproperties=font_prop, fontsize=10)
            plt.grid(True)
            plt.legend(prop=font_prop)
            plt.ylim(lean_center - (max_range/2 + padding), lean_center + (max_range/2 + padding))

            # 脂肪量のプロット
            plt.subplot(2, 2, 4)
            plt.plot(df['date'], df['fat_mass'], 'o-', color='purple', label='脂肪量', alpha=0.5)
            plt.plot(df['date'], df['fat_mass_ma5'], '-', color='darkmagenta', label='5日移動平均')
            plt.plot(df['date'], df['fat_mass_ma14'], '-', color='indigo', label='14日移動平均', linewidth=2)
            plt.title('脂肪量推移', fontproperties=font_prop, fontsize=12)
            plt.xlabel('日付', fontproperties=font_prop, fontsize=10)
            plt.ylabel('脂肪量 (kg)', fontproperties=font_prop, fontsize=10)
            plt.grid(True)
            plt.legend(prop=font_prop)
            plt.ylim(fat_center - (max_range/2 + padding), fat_center + (max_range/2 + padding))
            
            plt.tight_layout()
            plt.savefig('fitness_progress.png', dpi=100, bbox_inches='tight')
            plt.close()
            
            print("グラフを 'fitness_progress.png' として保存しました。")
            
        except Exception as e:
            print(f"グラフの生成中にエラーが発生しました: {str(e)}")
            import traceback
            traceback.print_exc()

def main():
    try:
        tracker = SimpleFitnessTracker()
        
        while True:
            print("\n=== フィットネストラッカー ===")
            print("1: 新しい記録を追加")
            print("2: 統計情報を表示")
            print("3: グラフを表示")
            print("4: 本日の状況を表示")
            print("5: 終了")
            
            choice = input("選択してください (1-5): ")
            
            if choice == '1':
                tracker.add_record()
            elif choice == '2':
                tracker.show_stats()
            elif choice == '3':
                tracker.plot_progress()
            elif choice == '4':
                if tracker.records:
                    tracker.show_daily_stats(tracker.records[-1])
                else:
                    print("記録がありません。")
            elif choice == '5':
                break
            else:
                print("正しい選択肢を入力してください。")
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()