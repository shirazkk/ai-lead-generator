interface StatsBarProps {
  total: number;
  avgScore: number;
  highScoreCount: number;
}

export default function StatsBar({ total, avgScore, highScoreCount }: StatsBarProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <div className="bg-gray-800 rounded-lg p-6 shadow-lg border border-gray-700">
        <div className="flex items-center gap-3">
          <span className="text-3xl">📊</span>
          <div>
            <p className="text-gray-400 text-sm">Total Leads</p>
            <p className="text-2xl font-bold text-white">{total}</p>
          </div>
        </div>
      </div>

      <div className="bg-gray-800 rounded-lg p-6 shadow-lg border border-gray-700">
        <div className="flex items-center gap-3">
          <span className="text-3xl">📈</span>
          <div>
            <p className="text-gray-400 text-sm">Avg Score</p>
            <p className="text-2xl font-bold text-white">
              {avgScore > 0 ? avgScore.toFixed(1) : '0.0'}
            </p>
          </div>
        </div>
      </div>

      <div className="bg-gray-800 rounded-lg p-6 shadow-lg border border-gray-700">
        <div className="flex items-center gap-3">
          <span className="text-3xl">⭐</span>
          <div>
            <p className="text-gray-400 text-sm">High Score</p>
            <p className="text-2xl font-bold text-white">{highScoreCount}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
