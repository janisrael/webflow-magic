<?php
/*
 * Template Name: Style Guide
 *
 * @package WebflowStarter
 */


get_header(); ?>

	<div id="primary" class="content-area">
		<main id="main" class="site-main">

			<?php
			while ( have_posts() ) : the_post(); ?>
				<div class="container w-container ">
					<div class="style-guide-wrap">
    <div class="style-guide-section">
      <h1 class="style-guide-title">Typography</h1>
      <div class="style-guide-content w-container">
        <p class="style-guide-subhead">You&#x27;ll see that these typography elements don&#x27;t have classes. That&#x27;s because on this page, we want to edit the styles after selecting &quot;All H1 Headings&quot; for example, so that it will effect all the elements on the site. To do this, select the H1 below, click where it says &quot;Select a Class or Tag&quot; and select &quot;All H1 Headings&quot; at the bottom of the list.</p>
        <div class="w-row">
          <div class="type-column-1 w-col w-col-6">
            <h1>If you edit styles here, they will change across the site</h1>
            <div class="style-guide-divider"></div>
            <div class="style-guide-label">H1</div>
            <h2>Lorem ipsum dolor sit amet</h2>
            <div class="style-guide-divider"></div>
            <div class="style-guide-label">H2</div>
            <h3>Lorem ipsum dolor sit amet</h3>
            <div class="style-guide-divider"></div>
            <div class="style-guide-label">H3</div>
            <h4>Lorem ipsum dolor sit amet</h4>
            <div class="style-guide-divider"></div>
            <div class="style-guide-label">H4</div>
            <h5>Lorem ipsum dolor sit amet</h5>
            <div class="style-guide-divider"></div>
            <div class="style-guide-label">H5</div>
            <h6>Lorem ipsum dolor sit amet</h6>
            <div class="style-guide-divider"></div>
            <div class="style-guide-label">H6</div>
          </div>
          <div class="type-column-2 w-col w-col-6">
            <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse varius enim in eros elementum tristique. Duis cursus, mi quis viverra ornare, eros dolor interdum nulla, ut commodo diam libero vitae erat.</p>
            <div class="style-guide-divider"></div>
            <div class="style-guide-label">Paragraph</div>
            <blockquote>Lorem ipsum dolor sit amet</blockquote>
            <div class="style-guide-divider"></div>
            <div class="style-guide-label">Block Quote</div><a href="#">Lorem ipsum</a>
            <div class="style-guide-divider"></div>
            <div class="style-guide-label">Text Link</div><a href="#" class="button w-button">View Project</a>
            <div class="style-guide-label">Button</div>
          </div>
        </div>
      </div>
    </div>
    <div class="style-guide-section">
      <h1 class="style-guide-title">Color</h1>
      <div class="style-guide-content w-container">
        <p class="style-guide-subhead">These colors have been created using Global Swatches. If you edit the Global Swatch color, it will change every element that uses that color swatch.</p>
        <h4>Text colors</h4>
        <div class="style-guide-divider"></div>
        <div class="w-row">
          <div class="w-col w-col-6">
            <div class="cc-font-color-dark color-block"></div>
            <div class="cc-box style-guide-label">
              <div>font color - dark</div>
              <div>#222222</div>
            </div>
          </div>
          <div class="w-col w-col-6">
            <div class="cc-font-color-light color-block"></div>
            <div class="cc-box style-guide-label">
              <div>font color - dark</div>
              <div>#aaaaaa</div>
            </div>
          </div>
        </div>
        <h4>Main colors</h4>
        <div class="style-guide-divider"></div>
        <div class="w-row">
          <div class="w-col w-col-6">
            <div class="cc-brand-color-1 color-block"></div>
            <div class="cc-box style-guide-label">
              <div>BRAND COLOR 1</div>
              <div>#3898ec</div>
            </div>
            <div class="cc-brand-color-3 color-block"></div>
            <div class="cc-box style-guide-label">
              <div>BRAND COLOR 3</div>
              <div>#63ecc0</div>
            </div>
          </div>
          <div class="w-col w-col-6">
            <div class="cc-brand-color-2 color-block"></div>
            <div class="cc-box style-guide-label">
              <div>BRAND COLOR 2</div>
              <div>#c860db</div>
            </div>
            <div class="cc-brand-color-4 color-block"></div>
            <div class="cc-box style-guide-label">
              <div>BRAND COLOR 4</div>
              <div>#ffb08b</div>
            </div>
          </div>
        </div>
        <h4>Neutral colors</h4>
        <div class="style-guide-divider"></div>
        <div class="w-row">
          <div class="w-col w-col-6">
            <div class="cc-light-grey-1 color-block"></div>
            <div class="cc-box style-guide-label">
              <div>LIGHT GREY 1</div>
              <div>#ebebeb</div>
            </div>
            <div class="cc-dark-grey-1 color-block"></div>
            <div class="cc-box style-guide-label">
              <div>DARK GREY 1</div>
              <div>#636363</div>
            </div>
          </div>
          <div class="w-col w-col-6">
            <div class="cc-light-grey-2 color-block"></div>
            <div class="cc-box style-guide-label">
              <div>LIGHT GREY 2</div>
              <div>#cccccc</div>
            </div>
            <div class="cc-dark-grey-2 color-block"></div>
            <div class="cc-box style-guide-label">
              <div>DARK GREY 2</div>
              <div>#333333</div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="style-guide-section">
      <h1 class="style-guide-title">Logo</h1>
      <div class="style-guide-content w-container">
        <p class="style-guide-subhead">These are sample logo SVGs that can be downloaded straight from the site, or you could set up a download link that links with the file that&#x27;s hosted with your cloud storage application of choice.</p>
        <div class="w-row">
          <div class="w-col w-col-6">
            <div class="cc-light style-guide-logo-box"><img src="/wp-content/themes/webflowstarter/images/sample-logo-black.svg"></div>
            <div class="cc-box style-guide-label">
              <div>MAIN LOGO BLACK</div><a href="#" target="_blank" class="style-guide-label-link">DOWNLOAD</a></div>
            <div class="cc-light style-guide-logo-box"><img src="/wp-content/themes/webflowstarter/images/sample-logo-stack-black.svg" width="190"></div>
            <div class="cc-box style-guide-label">
              <div>MAIN LOGO BLACK</div><a href="#" target="_blank" class="style-guide-label-link">DOWNLOAD</a></div>
          </div>
          <div class="w-col w-col-6">
            <div class="cc-dark style-guide-logo-box"><img src="/wp-content/themes/webflowstarter/images/sample-logo-white.svg"></div>
            <div class="cc-box style-guide-label">
              <div>MAIN LOGO WHITE</div><a href="#" target="_blank" class="style-guide-label-link">DOWNLOAD</a></div>
            <div class="cc-dark style-guide-logo-box"><img src="/wp-content/themes/webflowstarter/images/sample-logo-stack-white.svg" width="190"></div>
            <div class="cc-box style-guide-label">
              <div>MAIN LOGO WHITE</div><a href="#" target="_blank" class="style-guide-label-link">DOWNLOAD</a></div>
          </div>
        </div>
      </div>
    </div>
    <div class="style-guide-section">
      <h1 class="style-guide-title">Components</h1>
      <div class="style-guide-content w-container">
        <p class="style-guide-subhead">These are a few example components.</p>
        <div class="w-row">
          <div class="w-col w-col-6">
            <div class="w-form">
              <form id="email-form" name="email-form" data-name="Email Form">
                <h6>Name</h6><input type="text" id="name" name="name" data-name="Name" placeholder="Enter your name" maxlength="256" class="input w-input">
                <h6>Email</h6><input type="email" class="input w-input" maxlength="256" name="email" data-name="Email" placeholder="Enter your email address" id="email" required="">
                <h6>Message</h6><textarea id="field" name="field" placeholder="Example Text" maxlength="5000" class="cc-long input w-input"></textarea><input type="submit" value="Submit" data-wait="Please wait..." class="button w-button"></form>
              <div class="success-message w-form-done">
                <div>Thank you! Your submission has been received!</div>
              </div>
              <div class="error-message w-form-fail">
                <div>Oops! Something went wrong while submitting the form</div>
              </div>
            </div>
          </div>
          <div class="w-col w-col-6">
            <div data-duration-in="300" data-duration-out="100" class="tabs w-tabs">
              <div class="tab-menu w-tab-menu">
                <a data-w-tab="Tab 1" class="tab-link w--current w-inline-block w-tab-link">
                  <div>Tab 1</div>
                </a>
                <a data-w-tab="Tab 2" class="tab-link w-inline-block w-tab-link">
                  <div>Tab 2</div>
                </a>
                <a data-w-tab="Tab 3" class="tab-link w-inline-block w-tab-link">
                  <div>Tab 3</div>
                </a>
              </div>
              <div class="tabs-content w-tab-content">
                <div data-w-tab="Tab 1" class="tab-pane w--tab-active w-tab-pane">
                  <h3 class="card-title">Heading</h3>
                  <p class="card-paragraph">Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse varius enim in eros elementum tristique.</p>
                </div>
                <div data-w-tab="Tab 2" class="tab-pane w-tab-pane">
                  <h3 class="card-title">Heading</h3>
                  <p class="card-paragraph">Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse varius enim in eros elementum tristique.</p>
                </div>
                <div data-w-tab="Tab 3" class="tab-pane w-tab-pane">
                  <h3 class="card-title">Heading</h3>
                  <p class="card-paragraph">Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse varius enim in eros elementum tristique.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="card-container">
          <div class="card-wrap">
            <a href="#" class="card w-inline-block">
              <h3 class="card-title">Heading</h3>
              <p class="card-paragraph">Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse varius enim in eros elementum tristique.</p>
            </a>
          </div>
          <div class="card-wrap">
            <a href="#" class="card w-inline-block">
              <h3 class="card-title">Heading</h3>
              <p class="card-paragraph">Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse varius enim in eros elementum tristique.</p>
            </a>
          </div>
          <div class="card-wrap">
            <a href="#" class="card w-inline-block">
              <h3 class="card-title">Heading</h3>
              <p class="card-paragraph">Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse varius enim in eros elementum tristique.</p>
            </a>
          </div>
          <div class="card-wrap">
            <a href="#" class="card w-inline-block">
              <h3 class="card-title">Heading</h3>
              <p class="card-paragraph">Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse varius enim in eros elementum tristique.</p>
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>
				</div>
			<?php endwhile; // End of the loop.?>


		</main><!-- #main -->
	</div><!-- #primary -->

<?php

get_footer();
