import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const WeightSimulation = () => {
  // シミュレーションデータの生成
  const generateData = () => {
    const startDate = new Date('2023-10-26');
    const data = [];
    let currentWeight = 68;
    let currentBodyFat = 24;
    
    // 24週間（168日）のデータを生成
    for (let i = 0; i <= 168; i++) {
      const date = new Date(startDate.getTime() + i * 24 * 60 * 60 * 1000);
      
      // 体重減少のシミュレーション（非線形な減少を表現）
      const weightLoss = 10 * (1 - Math.exp(-i/120)); // 徐々に減少率が低下
      const simulatedWeight = 68 - weightLoss;
      
      // 体脂肪率の減少（体重より若干遅れて減少）
      const fatLoss = 10 * (1 - Math.exp(-(i-7)/100));
      const simulatedBodyFat = 24 - fatLoss;
      
      data.push({
        date: date.toLocaleDateString(),
        weight: simulatedWeight.toFixed(1),
        bodyFat: simulatedBodyFat.toFixed(1)
      });
    }
    return data;
  };

  const data = generateData();

  return (
    <div className="w-full max-w-4xl p-4">
      <h2 className="text-xl font-bold mb-4">体重・体脂肪率推移シミュレーション</h2>
      <div className="h-96">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="date" 
              tick={{fontSize: 12}}
              interval={20}
            />
            <YAxis 
              yAxisId="weight"
              domain={[55, 70]}
              tick={{fontSize: 12}}
              label={{ value: '体重 (kg)', angle: -90, position: 'insideLeft' }}
            />
            <YAxis 
              yAxisId="bodyFat"
              orientation="right"
              domain={[10, 25]}
              tick={{fontSize: 12}}
              label={{ value: '体脂肪率 (%)', angle: 90, position: 'insideRight' }}
            />
            <Tooltip />
            <Legend />
            <Line 
              yAxisId="weight"
              type="monotone" 
              dataKey="weight" 
              stroke="#8884d8" 
              name="体重"
              dot={false}
            />
            <Line 
              yAxisId="bodyFat"
              type="monotone" 
              dataKey="bodyFat" 
              stroke="#82ca9d" 
              name="体脂肪率"
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-4">
        <p className="text-sm text-gray-600">
          ※このシミュレーションは理想的な進捗を示しています。
          実際の減量では、体調や生活リズムにより変動が生じる可能性があります。
        </p>
      </div>
    </div>
  );
};

export default WeightSimulation;