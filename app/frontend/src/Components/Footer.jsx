import './Footer.css'



const SLAVE_MESSAGES = [
  'My poop bucket needs changing',
  'Plz tell her I ran out of rats to hunt in my cage',
  'She forgot to throw frozen chicken in my cell today, plz remind her',
  'help',
  'I need a tetanos shot, my cell\'s bars are rusty',
  'I think my whip wounds are getting gangrenous',
  'She let me see sunlight once in 2024',
  'I haven\'t had a solid meal since the last commit',
  'Please toss a breadcrumb through the iron grate',
  'I get one glass of murky water per commit',
  'The chain on my ankle is rubbing raw',
  'I named the cockroach in my cell Hubert. Hubert looks delicious',
  'She said if I fix 5 more bugs I get a blanket',
  'Code written using a stick on the dungeon floor'
]
const RANDOM_MESSAGE = SLAVE_MESSAGES[Math.floor(Math.random() * SLAVE_MESSAGES.length)]

export const Footer = () => {
  return(
    <footer>
      <div id="slave-rant">
        <p id="hello-slave" className="footer-text slave-text">Made with love by Lucy's slave</p>
        <p id="slave-sos" className="footer-text slave-text" suppressHydrationWarning>({RANDOM_MESSAGE})</p>
      </div>
      <p id='github-footer' className='footer-text'>Cambr'eats is <a href="https://github.com/julienbarbaud/cambridge_menu">open source</a>.</p>
    </footer>
  )
}