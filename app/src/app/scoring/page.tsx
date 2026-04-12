export default function ScoringPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-2">Poomsae Scoring</h1>
      <p className="text-sm text-gray-500 mb-8">
        Based on WT Poomsae Competition Rules, Article 15-16 (September 2024)
      </p>

      {/* Score breakdown */}
      <section className="mb-10">
        <h2 className="text-xl font-semibold mb-4">
          Recognized Poomsae &mdash; 10.0 Total
        </h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {/* Accuracy */}
          <div className="bg-white rounded-lg border border-gray-200 p-5">
            <div className="flex items-baseline justify-between mb-3">
              <h3 className="text-lg font-semibold text-blue-700">Accuracy</h3>
              <span className="text-2xl font-bold text-blue-700">4.0</span>
            </div>
            <ul className="space-y-2 text-sm text-gray-700">
              <li className="flex items-start gap-2">
                <span className="mt-1 w-1.5 h-1.5 rounded-full bg-blue-400 shrink-0" />
                <span>
                  <span className="font-medium">Basic movements accuracy</span>{" "}
                  &mdash; correct technique shape and trajectory
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-1 w-1.5 h-1.5 rounded-full bg-blue-400 shrink-0" />
                <span>
                  <span className="font-medium">
                    Individual movement accuracy
                  </span>{" "}
                  &mdash; details of each stance, block, strike
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-1 w-1.5 h-1.5 rounded-full bg-blue-400 shrink-0" />
                <span>
                  <span className="font-medium">Balance</span> &mdash;
                  stability throughout transitions
                </span>
              </li>
            </ul>
          </div>

          {/* Presentation */}
          <div className="bg-white rounded-lg border border-gray-200 p-5">
            <div className="flex items-baseline justify-between mb-3">
              <h3 className="text-lg font-semibold text-emerald-700">
                Presentation
              </h3>
              <span className="text-2xl font-bold text-emerald-700">6.0</span>
            </div>
            <ul className="space-y-2 text-sm text-gray-700">
              <li className="flex items-start gap-2">
                <span className="mt-1 w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0" />
                <span>
                  <span className="font-medium">Speed &amp; Power</span>{" "}
                  <span className="text-gray-400">(2.0)</span> &mdash; dynamic
                  tempo changes, impact on techniques
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-1 w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0" />
                <span>
                  <span className="font-medium">Rhythm &amp; Tempo</span>{" "}
                  <span className="text-gray-400">(2.0)</span> &mdash; proper
                  pacing, smooth transitions between fast and slow
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-1 w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0" />
                <span>
                  <span className="font-medium">Expression of Energy</span>{" "}
                  <span className="text-gray-400">(2.0)</span> &mdash; ki,
                  breathing, focus, and spirit
                </span>
              </li>
            </ul>
          </div>
        </div>
      </section>

      {/* Deductions */}
      <section className="mb-10">
        <h2 className="text-xl font-semibold mb-4">Deductions (Article 16)</h2>
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <div className="grid grid-cols-[auto_1fr] text-sm">
            <div className="px-4 py-3 bg-amber-50 border-b border-gray-200 font-semibold text-amber-800">
              &minus;0.1
            </div>
            <div className="px-4 py-3 border-b border-gray-200">
              <span className="font-medium text-gray-900">Small mistake</span>
              <span className="text-gray-500">
                {" "}
                &mdash; minor stance detail, slight hand position error
              </span>
            </div>

            <div className="px-4 py-3 bg-orange-50 border-b border-gray-200 font-semibold text-orange-800">
              &minus;0.3
            </div>
            <div className="px-4 py-3 border-b border-gray-200">
              <span className="font-medium text-gray-900">Big mistake</span>
              <span className="text-gray-500">
                {" "}
                &mdash; wrong technique, 3+ second pause, missing kihap, foot
                touches ground, loud breathing
              </span>
            </div>

            <div className="px-4 py-3 bg-red-50 font-semibold text-red-800">
              &minus;0.6
            </div>
            <div className="px-4 py-3">
              <span className="font-medium text-gray-900">Restart</span>
              <span className="text-gray-500">
                {" "}
                &mdash; athlete stops and begins the poomsae again
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* Common deductions */}
      <section>
        <h2 className="text-xl font-semibold mb-4">Common Deductions</h2>
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 text-left text-xs text-gray-500 uppercase tracking-wide">
                <th className="px-4 py-2.5 font-medium">What Happens</th>
                <th className="px-4 py-2.5 font-medium">Category</th>
                <th className="px-4 py-2.5 font-medium text-right">
                  Deduction
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              <tr>
                <td className="px-4 py-2.5 text-gray-700">
                  Front foot turned inward in front stance
                </td>
                <td className="px-4 py-2.5 text-gray-500">Small</td>
                <td className="px-4 py-2.5 text-right font-medium text-amber-700">
                  &minus;0.1
                </td>
              </tr>
              <tr className="bg-gray-50/50">
                <td className="px-4 py-2.5 text-gray-700">
                  Fist not fully chambered at the hip
                </td>
                <td className="px-4 py-2.5 text-gray-500">Small</td>
                <td className="px-4 py-2.5 text-right font-medium text-amber-700">
                  &minus;0.1
                </td>
              </tr>
              <tr>
                <td className="px-4 py-2.5 text-gray-700">
                  Looking down instead of at the target
                </td>
                <td className="px-4 py-2.5 text-gray-500">Small</td>
                <td className="px-4 py-2.5 text-right font-medium text-amber-700">
                  &minus;0.1
                </td>
              </tr>
              <tr className="bg-gray-50/50">
                <td className="px-4 py-2.5 text-gray-700">
                  Block/strike height clearly wrong (e.g., low block at mid
                  level)
                </td>
                <td className="px-4 py-2.5 text-gray-500">Big</td>
                <td className="px-4 py-2.5 text-right font-medium text-orange-700">
                  &minus;0.3
                </td>
              </tr>
              <tr>
                <td className="px-4 py-2.5 text-gray-700">
                  Performing a different technique than required
                </td>
                <td className="px-4 py-2.5 text-gray-500">Big</td>
                <td className="px-4 py-2.5 text-right font-medium text-orange-700">
                  &minus;0.3
                </td>
              </tr>
              <tr className="bg-gray-50/50">
                <td className="px-4 py-2.5 text-gray-700">
                  Forgetting and pausing 3+ seconds
                </td>
                <td className="px-4 py-2.5 text-gray-500">Big</td>
                <td className="px-4 py-2.5 text-right font-medium text-orange-700">
                  &minus;0.3
                </td>
              </tr>
              <tr>
                <td className="px-4 py-2.5 text-gray-700">
                  Missing kihap at the designated move
                </td>
                <td className="px-4 py-2.5 text-gray-500">Big</td>
                <td className="px-4 py-2.5 text-right font-medium text-orange-700">
                  &minus;0.3
                </td>
              </tr>
              <tr className="bg-gray-50/50">
                <td className="px-4 py-2.5 text-gray-700">
                  Foot touches ground during a kick
                </td>
                <td className="px-4 py-2.5 text-gray-500">Big</td>
                <td className="px-4 py-2.5 text-right font-medium text-orange-700">
                  &minus;0.3
                </td>
              </tr>
              <tr>
                <td className="px-4 py-2.5 text-gray-700">
                  Audible loud breathing during performance
                </td>
                <td className="px-4 py-2.5 text-gray-500">Big</td>
                <td className="px-4 py-2.5 text-right font-medium text-orange-700">
                  &minus;0.3
                </td>
              </tr>
              <tr className="bg-gray-50/50">
                <td className="px-4 py-2.5 text-gray-700">
                  Stopping and restarting the poomsae
                </td>
                <td className="px-4 py-2.5 text-gray-500">Restart</td>
                <td className="px-4 py-2.5 text-right font-medium text-red-700">
                  &minus;0.6
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
