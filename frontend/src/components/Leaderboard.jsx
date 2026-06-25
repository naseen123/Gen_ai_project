import MemberCard from './MemberCard'

export default function Leaderboard({ members, onSelectMember, selectedMember }) {
  const sorted = [...members].sort((a, b) => (b.overall_score ?? 0) - (a.overall_score ?? 0))

  return (
    <div className="space-y-3 animate-fade-in">
      <h2 className="text-xl font-bold font-heading gradient-text mb-4">Team Leaderboard</h2>
      {sorted.map((member, i) => (
        <MemberCard
          key={member.name}
          member={member}
          rank={i + 1}
          selected={selectedMember?.name === member.name}
          onClick={onSelectMember}
        />
      ))}
    </div>
  )
}
