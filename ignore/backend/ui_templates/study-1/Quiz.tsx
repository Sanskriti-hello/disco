import React, { useState } from "react";

interface QuizQ {
  question: string;
  options: {
    A: string;
    B: string;
    C: string;
    D: string;
  };
  answer: "A" | "B" | "C" | "D";
}

export default function Quiz({ questions }: { questions: QuizQ[] }) {
  const [selected, setSelected] = useState<Record<number, string>>({});

  return (
    <div className="bg-white rounded-xl shadow p-6">
      <h2 className="text-lg font-semibold mb-4">🎯 Quiz</h2>

      <div className="space-y-6">
        {questions.map((q, idx) => (
          <div key={idx}>
            <p className="font-medium mb-2">
              {idx + 1}. {q.question}
            </p>

            <div className="space-y-2">
              {Object.entries(q.options).map(([key, value]) => {
                const isSelected = selected[idx] === key;
                const isCorrect = key === q.answer;

                return (
                  <button
                    key={key}
                    onClick={() =>
                      setSelected({ ...selected, [idx]: key })
                    }
                    className={`w-full text-left px-4 py-2 rounded border
                      ${isSelected ? "border-blue-500 bg-blue-50" : "border-gray-200"}
                      ${isSelected && isCorrect ? "bg-green-100 border-green-500" : ""}
                      ${isSelected && !isCorrect ? "bg-red-100 border-red-500" : ""}
                    `}
                  >
                    <span className="font-semibold mr-2">{key}.</span>
                    {value}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
