import { Users, BookOpen, Calendar, Clock } from 'lucide-react'

const stats = [
  { name: 'Total People', value: '0', icon: Users },
  { name: 'Anecdotes', value: '0', icon: BookOpen },
  { name: 'Upcoming Birthdays', value: '0', icon: Calendar },
  { name: 'Recent Contacts', value: '0', icon: Clock },
]

export function Dashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Dashboard</h2>
        <p className="text-muted-foreground">
          Welcome to LifeGraph, your personal relationship memory.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <div
            key={stat.name}
            className="bg-card border rounded-lg p-6 flex items-center gap-4"
          >
            <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center">
              <stat.icon className="h-6 w-6 text-primary" />
            </div>
            <div>
              <p className="text-2xl font-bold">{stat.value}</p>
              <p className="text-sm text-muted-foreground">{stat.name}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-card border rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Recent Anecdotes</h3>
          <div className="text-muted-foreground text-sm">
            No anecdotes yet. Start by adding people and memories!
          </div>
        </div>

        <div className="bg-card border rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Upcoming Birthdays</h3>
          <div className="text-muted-foreground text-sm">
            No upcoming birthdays in the next 30 days.
          </div>
        </div>
      </div>
    </div>
  )
}
